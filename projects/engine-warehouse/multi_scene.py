"""USD view for unique engine/pallet/carrier instances. Model is in MultiCycle."""
from pxr import Usd,UsdGeom,Gf,Sdf
from u_storage_scene import StorageScene,FOLDER
from pathlib import Path
HERE=Path(__file__).resolve().parent

class MultiScene:
    def __init__(self,stage):
        self.stage=stage;self.robot=StorageScene(stage);self.cache={};self.engines={};self.pallets={};self.carriers={}
        for path in ('/World/InlineLoad','/World/CarriedEngine','/World/OutboundCarrier'):stage.OverridePrim(path).SetActive(False)
        for name in ('E1','E2','E3'):
            self.engines[name]=self.make('/World/Engines/'+name,FOLDER/'engine_supported_preview.usda',('InlinePallet','Fixture/Columns','Light','PreviewCamera'))
            self.pallets[name]=self.make('/World/InlinePallets/'+name,FOLDER/'engine_supported_preview.usda',('Engine','Fixture/Receivers','Light','PreviewCamera'))
        for name in ('C1','C2','C3','C4'):
            self.carriers[name]=self.make('/World/Carriers/'+name,HERE/'assets/outbound_frame_pallet.usda',())
        self.event=stage.GetDefaultPrim().CreateAttribute('demo:scenarioPhase',Sdf.ValueTypeNames.String)
    def make(self,path,asset,disabled):
        root=UsdGeom.Xform.Define(self.stage,path);root.GetPrim().GetReferences().AddReference(str(asset))
        for name in disabled:self.stage.OverridePrim(path+'/'+name).SetActive(False)
        return (root.AddTranslateOp(),root.AddRotateZOp(),UsdGeom.Imageable(root).CreateVisibilityAttr())
    def set(self,op,value):
        key=str(op.GetAttr().GetPath()) if hasattr(op,'GetAttr') else str(op.GetPath())
        if self.cache.get(key)!=value:op.Set(value);self.cache[key]=value
    def apply(self,model):
        import math
        for op,q,sign in zip(self.robot.joints,model.robot_frame.q,(1,1,-1,-1,-1,-1)):self.set(op,math.degrees(float(q))*sign)
        for sign,op in zip((1,-1),self.robot.jaws):self.set(op,Gf.Vec3d(0,sign*model.robot_frame.opening,0))
        for name,e in model.engines.items():
            xyz,yaw,vis=self.engines[name];self.set(xyz,Gf.Vec3d(*e['position']));self.set(yaw,float(e['yaw']));self.set(vis,'inherited' if e.get('visible',True) else 'invisible')
            xyz,yaw,vis=self.pallets[name];self.set(xyz,Gf.Vec3d(*e['pallet_position']));self.set(vis,'inherited' if e['pallet_visible'] else 'invisible')
        for name,c in model.carriers.items():
            xyz,yaw,vis=self.carriers[name];self.set(xyz,Gf.Vec3d(*c['position']))
            rail=self.stage.GetPrimAtPath('/World/Carriers/'+name+'/SideRail0').GetAttribute('xformOp:translate')
            self.set(rail,Gf.Vec3d(-.53,0,.93-.70*c['gate_open']))
        self.set(self.event,model.phase)
