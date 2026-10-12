"""Fixture-assisted pickup: explicit ideal pin/clamp lock, not friction-only grasp proof."""
import numpy as np
from pxr import Usd,UsdGeom,UsdPhysics,Gf,Sdf
from wrist_camera import TOOL
from pickup_correction import plan,joint_attributes,write_joints,fk,ik

def configure(stage):
    from pxr import PhysxSchema
    from scipy.spatial import ConvexHull
    engine=stage.GetPrimAtPath('/World/TestLoad/Engine')
    # One conservative convex envelope from the actual engine visual vertices.
    cache=UsdGeom.XformCache();inverse=cache.GetLocalToWorldTransform(engine).GetInverse()
    points=[]
    for p in Usd.PrimRange(engine):
        if p.IsA(UsdGeom.Mesh) and p.GetName()!='_ContactHull':
            a=np.asarray(UsdGeom.Mesh(p).GetPointsAttr().Get())
            m=np.asarray(cache.GetLocalToWorldTransform(p)*inverse)
            points.append(a@m[:3,:3]+m[3,:3])
    points=np.concatenate(points);hull=ConvexHull(points)
    # Remap hull indices to keep only surface vertices.
    ids=hull.vertices;lookup={int(v):i for i,v in enumerate(ids)}
    mesh=UsdGeom.Mesh.Define(stage,str(engine.GetPath())+'/_ContactHull')
    mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in points[ids]])
    mesh.CreateFaceVertexCountsAttr([3]*len(hull.simplices))
    mesh.CreateFaceVertexIndicesAttr([lookup[int(v)] for v in hull.simplices.ravel()])
    mesh.CreateVisibilityAttr('invisible')
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr('convexHull')
    UsdPhysics.RigidBodyAPI.Apply(engine).CreateRigidBodyEnabledAttr(True)
    UsdPhysics.MassAPI.Apply(engine).CreateMassAttr(1.) # normalized test body; not real engine mass
    phys=PhysxSchema.PhysxRigidBodyAPI.Apply(engine)
    phys.CreateSolverPositionIterationCountAttr(16);phys.CreateSolverVelocityIterationCountAttr(4)
    for root in ('/World/TestLoad/InlinePallet','/World/TestLoad/Fixture/Columns'):
        for p in Usd.PrimRange(stage.GetPrimAtPath(root)):
            if p.IsA(UsdGeom.Cube) or p.IsA(UsdGeom.Cylinder) or p.IsA(UsdGeom.Mesh):
                UsdPhysics.CollisionAPI.Apply(p)
                if p.IsA(UsdGeom.Mesh):UsdPhysics.MeshCollisionAPI.Apply(p).CreateApproximationAttr('convexHull')
    # Physics receiver holes are not modelled; receiver visuals remain visual only.
    for name in ('Left','Right'):
        root=stage.GetPrimAtPath(TOOL+'/'+name)
        body=UsdPhysics.RigidBodyAPI.Apply(root);body.CreateKinematicEnabledAttr(True)
        for p in Usd.PrimRange(root):
            if p.IsA(UsdGeom.Cube):UsdPhysics.CollisionAPI.Apply(p)
    scenes=[p for p in stage.Traverse() if p.IsA(UsdPhysics.Scene)]
    if len(scenes)>1:raise ValueError('HOLD: contact lab requires a single physics scene')
    scene=UsdPhysics.Scene(scenes[0]) if scenes else UsdPhysics.Scene.Define(stage,'/World/ContactPhysics')
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));scene.CreateGravityMagnitudeAttr(9.81)
    PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim()).CreateTimeStepsPerSecondAttr(120)
    return engine

class ContactTrial:
    def __init__(self,stage,result):
        self.stage=stage;self.result=result
        self.frames,self.target,self.yaw=plan(result,standoff=0.)
        self.engine=configure(stage);self.attrs=joint_attributes(stage)
        hull=UsdGeom.Mesh(stage.GetPrimAtPath(str(self.engine.GetPath())+'/_ContactHull'))
        bounds=np.asarray(hull.GetPointsAttr().Get())
        self.center=Gf.Vec3d(*map(float,(bounds.min(axis=0)+bounds.max(axis=0))/2))
        # Abstract the production locating fixture only until jaws have closed.
        # The pallet lock hands over to an ideal pin/clamp joint before lift.
        fixture=UsdPhysics.FixedJoint.Define(stage,'/World/InitialFixtureLock')
        fixture.CreateBody1Rel().SetTargets([self.engine.GetPath()])
        transform=UsdGeom.Xformable(self.engine).ComputeLocalToWorldTransform(0)
        fixture.CreateLocalPos0Attr(Gf.Vec3f(*transform.ExtractTranslation()))
        fixture.CreateLocalRot0Attr(Gf.Quatf(transform.ExtractRotationQuat()))
        self.fixture=fixture
        self.grip=None;self.fixture_released=False;self.pose_samples=[]
        self.jaws=[stage.GetPrimAtPath(TOOL+'/'+n).GetAttribute('xformOp:translate') for n in ('Left','Right')]
        self.dt=1/120;self.time=0.;self.history=[]
    def opening(self,value):
        for sign,a in zip((1,-1),self.jaws):a.Set(Gf.Vec3d(0,sign*value,0))
    def position(self):
        return np.array(UsdGeom.Xformable(self.engine).ComputeLocalToWorldTransform(0).Transform(self.center))
    def rotation(self):
        q=UsdGeom.Xformable(self.engine).ComputeLocalToWorldTransform(0).ExtractRotationQuat().GetNormalized()
        return np.array([q.GetReal(),*q.GetImaginary()])
    def pose_error(self):
        angle=float(np.degrees(2*np.arccos(np.clip(abs(np.dot(self.rotation(),self.initial_rotation)),0,1))))
        xy=float(np.linalg.norm((self.position()-self.initial)[:2]))
        return angle,xy
    def lock_gripper(self):
        # Capture the existing engine pose: no snap to a nominal alignment.
        jaw=self.stage.GetPrimAtPath(TOOL+'/Left')
        body=UsdGeom.Xformable(self.engine).ComputeLocalToWorldTransform(0)
        local=body*UsdGeom.Xformable(jaw).ComputeLocalToWorldTransform(0).GetInverse()
        joint=UsdPhysics.FixedJoint.Define(self.stage,'/World/IdealPinClampLock')
        joint.CreateBody0Rel().SetTargets([jaw.GetPath()])
        joint.CreateBody1Rel().SetTargets([self.engine.GetPath()])
        joint.CreateLocalPos0Attr(Gf.Vec3f(*local.ExtractTranslation()))
        joint.CreateLocalRot0Attr(Gf.Quatf(local.ExtractRotationQuat()))
        joint.CreateCollisionEnabledAttr(False)
        self.grip=joint
    def steps(self,close=True):
        # Yield exactly one physics tick per iteration; engine transforms are never assigned.
        for _ in range(120):yield 'SETTLE'
        self.initial=self.position()
        self.initial_rotation=self.rotation()
        for (_,q0),(end,q1) in zip(self.frames,self.frames[1:]):
            n=max(1,round((end-self.time_motion)*120)) if hasattr(self,'time_motion') else 5
            for a in np.linspace(0,1,n+1)[1:]:write_joints(self.attrs,q0+a*(q1-q0));yield 'APPROACH'
            self.time_motion=end
        for a in np.linspace(0,1,240):
            self.opening(.12*(1-a) if close else .12);yield 'CLOSE' if close else 'OPEN_CONTROL'
            self.pose_samples.append(self.pose_error())
        if close:
            self.lock_gripper()
            yield 'CLAMP_LOCK'
            self.fixture.CreateJointEnabledAttr(False);self.fixture_released=True
        q=self.frames[-1][1].copy()
        for a in np.linspace(0,1,360):
            q=ik(self.target+np.array([0,0,.2*a]),self.yaw,q,(0,0,0));write_joints(self.attrs,q);yield 'LIFT'
            self.pose_samples.append(self.pose_error())
        self.hold=[]
        for _ in range(240):
            self.hold.append(self.position());yield 'HOLD'
            self.pose_samples.append(self.pose_error())
        self.lifted=self.position()
        for a in np.linspace(0,1,360):
            q=ik(self.target+np.array([0,0,.2*(1-a)]),self.yaw,q,(0,0,0));write_joints(self.attrs,q);yield 'LOWER'
            self.pose_samples.append(self.pose_error())
        self.seat_error=float(np.linalg.norm(self.position()-self.initial))
        self.seat_angle=self.pose_error()[0]
        if self.seat_error>.005 or self.seat_angle>.25:
            raise ValueError('HOLD: engine did not return to its locating fixture; jaws remain closed')
        self.fixture.CreateJointEnabledAttr(True)
        yield 'PALLET_LOCK'
        if self.grip:self.grip.CreateJointEnabledAttr(False)
        for a in np.linspace(0,1,180):self.opening(.12*a if close else .12);yield 'RELEASE'
        for _ in range(120):yield 'SEATED'
    def report(self):
        lift=float(self.lifted[2]-self.initial[2])
        slip=float(np.max(np.linalg.norm(np.asarray(self.hold)-self.hold[0],axis=1)))
        angle,xy=np.max(self.pose_samples,axis=0)
        return dict(lift_m=lift,hold_slip_m=slip,max_rotation_change_deg=float(angle),max_xy_shift_m=float(xy),
            reseat_error_m=self.seat_error,grasp_locked=self.grip is not None,fixture_released=self.fixture_released,
            success=self.fixture_released and lift>.19 and slip<.003 and angle<.25 and xy<.003 and self.seat_error<.005,
            scope='ideal pin/clamp fixed joint preserves measured pose; normalized 1kg body; not friction-only grasp, pin-hole fit or real force validation')
