"""Mesh-fitted support shoes; geometry checks, not force/contact dynamics."""
from pathlib import Path
from fanuc_kinematics import np,Rotation
# Engine-local centers. Tool axes are rotated 180 degrees about engine Z.
SITES=(("Right",.16,.13,.008,.005),("Left",.11,-.16,.008,.005))
ROOT=Path(__file__).resolve().parents[2]

def engine_triangles():
    from pxr import Usd,UsdGeom
    stage=Usd.Stage.Open(str(ROOT/'external_assets/engines/caterham_duratec/usd/engine_supported_preview.usda'))
    triangles=[]
    for prim in Usd.PrimRange(stage.GetPrimAtPath('/World/Engine')):
        if not prim.IsA(UsdGeom.Mesh):continue
        mesh=UsdGeom.Mesh(prim);v=np.asarray(mesh.GetPointsAttr().Get())
        matrix=np.array(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(0))
        v=(np.c_[v,np.ones(len(v))]@matrix)[:,:3]
        counts=mesh.GetFaceVertexCountsAttr().Get();indices=mesh.GetFaceVertexIndicesAttr().Get();start=0
        for count in counts:
            face=indices[start:start+count];start+=count
            triangles.extend(v[[face[0],face[i],face[i+1]]] for i in range(1,count-1))
    return np.asarray(triangles)

def underside(tri,x,y):
    a=tri[:,0];u=tri[:,1]-a;v=tri[:,2]-a;den=u[:,0]*v[:,1]-u[:,1]*v[:,0]
    safe=np.where(abs(den)>1e-12,den,1);px=x-a[:,0];py=y-a[:,1]
    b=(px*v[:,1]-py*v[:,0])/safe;c=(u[:,0]*py-u[:,1]*px)/safe
    hit=(abs(den)>1e-12)&(b>=0)&(c>=0)&(b+c<=1)
    if not hit.any():raise ValueError('No engine surface above support shoe')
    return float((a[:,2]+b*u[:,2]+c*v[:,2])[hit].min())

def validate_alignment(position,rotation,tool_position,tool_rotation):
    # Registration residual is tolerated up to 3 mm at both contact regions.
    # This checks the actual engine pose; it never corrects the commanded pose.
    expected_rotation=tool_rotation@Rotation.from_euler('z',180,degrees=True).as_matrix()
    expected_origin=tool_position+tool_rotation@np.array([.43,0,-.65])
    points=np.array([[x,y,z] for _,x,y,_,_ in SITES for z in (.15,.20)])
    errors=np.linalg.norm(points@rotation.T+position-(points@expected_rotation.T+expected_origin),axis=1)
    if errors.max()>.003:raise ValueError(f'Support contact misaligned: {errors.max()*1000:.2f} mm; pickup blocked')
    return float(errors.max())
