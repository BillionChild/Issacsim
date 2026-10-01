"""USD adapter shared by the offline checker and the live U-cell demo."""
from pathlib import Path
from pxr import Usd, UsdGeom, Gf, Sdf

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'external_assets/engines/caterham_duratec/usd'


class StorageScene:
    def __init__(self,stage):
        self.stage=stage
        for name in ('Engine','Fixture/Receivers'):
            stage.OverridePrim('/World/InlineLoad/'+name).SetActive(False)
        payload=UsdGeom.Xform.Define(stage,'/World/CarriedEngine')
        payload.GetPrim().GetReferences().AddReference(str(FOLDER/'engine_supported_preview.usda'))
        for name in ('InlinePallet','Fixture/Columns','Light','PreviewCamera'):
            stage.OverridePrim('/World/CarriedEngine/'+name).SetActive(False)
        self.payload=payload.AddTranslateOp();self.yaw=payload.AddRotateZOp()
        self.pallet=next(o for o in UsdGeom.Xformable(stage.GetPrimAtPath('/World/InlineLoad')).GetOrderedXformOps() if o.GetOpType()==UsdGeom.XformOp.TypeTranslate)
        self.joints=[];path='/World/Robot/Base'
        for i,axis in enumerate('ZYYXYX',1):
            path+=f'/J{i}'
            self.joints.append(stage.GetPrimAtPath(path).GetAttribute('xformOp:rotate'+axis))
        self.tool_path=path+'/EngineJig'
        self.jaws=[next(o for o in UsdGeom.Xformable(stage.GetPrimAtPath(self.tool_path+'/'+name)).GetOrderedXformOps() if o.GetOpType()==UsdGeom.XformOp.TypeTranslate) for name in ('Left','Right')]
        self.phase=stage.GetDefaultPrim().CreateAttribute('demo:phase',Sdf.ValueTypeNames.String)
        self.owner=stage.GetDefaultPrim().CreateAttribute('demo:payloadOwner',Sdf.ValueTypeNames.String)
        self.permission=stage.GetDefaultPrim().CreateAttribute('demo:pickupAllowed',Sdf.ValueTypeNames.Bool)
        self.occupied=stage.GetDefaultPrim().CreateAttribute('demo:cellOccupied',Sdf.ValueTypeNames.Bool)

    def apply(self,frame,pallet_position,pickup_allowed=False,occupied=False,time=Usd.TimeCode.Default()):
        import math
        for op,value,sign in zip(self.joints,frame.q,(1,1,-1,-1,-1,-1)):
            op.Set(math.degrees(float(value))*sign,time)
        for sign,op in zip((1,-1),self.jaws):op.Set(Gf.Vec3d(0,sign*frame.opening,0),time)
        self.pallet.Set(Gf.Vec3d(*pallet_position),time)
        self.payload.Set(Gf.Vec3d(*(pallet_position if frame.owner=='pallet' else frame.payload)),time)
        self.yaw.Set(float(frame.yaw),time)
        self.phase.Set(frame.phase,time);self.owner.Set(frame.owner,time)
        self.permission.Set(bool(pickup_allowed),time);self.occupied.Set(bool(occupied),time)
