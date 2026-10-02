"""USD adapter shared by the offline checker and the live U-cell demo."""
from pathlib import Path
from pxr import Usd, UsdGeom, Gf, Sdf

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'external_assets/engines/caterham_duratec/usd'


class StorageScene:
    def __init__(self,stage):
        self.stage=stage
        self._last={};self.writes=0
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
        # Cache only default values. Baked time samples must always be authored.
        def write(op,value):
            key=str(op.GetPath()) if hasattr(op,'GetPath') else str(op.GetAttr().GetPath())
            if time==Usd.TimeCode.Default() and key in self._last and self._last[key]==value:return
            op.Set(value,time);self.writes+=1
            if time==Usd.TimeCode.Default():self._last[key]=value
        for op,value,sign in zip(self.joints,frame.q,(1,1,-1,-1,-1,-1)):
            write(op,math.degrees(float(value))*sign)
        for sign,op in zip((1,-1),self.jaws):write(op,Gf.Vec3d(0,sign*frame.opening,0))
        write(self.pallet,Gf.Vec3d(*pallet_position))
        write(self.payload,Gf.Vec3d(*(pallet_position if frame.owner=='pallet' else frame.payload)))
        write(self.yaw,float(frame.yaw))
        write(self.phase,frame.phase);write(self.owner,frame.owner)
        write(self.permission,bool(pickup_allowed));write(self.occupied,bool(occupied))
