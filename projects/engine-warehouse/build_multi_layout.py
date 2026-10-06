"""Approved east-fed four-carrier L conveyor; preserves single-engine layout."""
from build_u_layout import stage,material,box,reference,FOLDER,HERE,UsdGeom,UsdShade,Gf,Sdf
OUTPUT=FOLDER/'warehouse_multi_layout.usda'

def build(empty_return=True):
    s=stage(OUTPUT,'/World')
    s.GetDefaultPrim().GetReferences().AddReference(str(FOLDER/'warehouse_u_layout_preview.usda'))
    s.GetDefaultPrim().CreateAttribute('demo:multiEngine',Sdf.ValueTypeNames.Bool).Set(True)
    s.OverridePrim('/World/Conveyors/Outbound').SetActive(False)
    steel=material(s,'MultiSteel',(.48,.52,.57),.8);blue=material(s,'MultiFrame',(.055,.15,.26),.5)
    def conveyor(name,axis,center,length,width=1.2):
        along=0 if axis=='X' else 1;cross=1-along;base='/World/Conveyors/'+name
        for i in range(round(length/.1)):
            pos=[*center,.67];pos[along]+=-length/2+(i+.5)*.1
            r=UsdGeom.Cylinder.Define(s,base+f'/Roller{i:03}');r.CreateAxisAttr('Y' if axis=='X' else 'X');r.CreateRadiusAttr(.03);r.CreateHeightAttr(width);r.AddTranslateOp().Set(Gf.Vec3d(*pos));UsdShade.MaterialBindingAPI.Apply(r.GetPrim()).Bind(steel)
        for sign in (-1,1):
            pos=[*center,.62];pos[cross]+=sign*(width/2+.04);size=[.08,.08,.12];size[along]=length
            box(s,base+f'/Frame{sign+1}',pos,size,blue)
            for end in (-1,1):
                leg=pos.copy();leg[along]+=end*(length/2-.12);leg[2]=.29;box(s,base+f'/Leg{sign+1}_{end+1}',leg,(.08,.08,.58),blue)
    conveyor('EmptyCarrierFeed','X',(5.3,0),4.4)
    conveyor('LoadedCarrierBuffer','Y',(2.5,3.3),5.4)
    box(s,'/World/Conveyors/CarrierTransfer',(2.5,0,.65),(1.2,1.2,.1),steel)
    if empty_return:conveyor('EmptyInlineReturn','X',(-3.5,-3.6),2.,.9)
    # Broader view includes empty-carrier queue and north accumulation.
    cam=UsdGeom.Camera(s.GetPrimAtPath('/World/PreviewCamera'))
    xf=UsdGeom.Xformable(cam);xf.ClearXformOpOrder();xf.AddTranslateOp().Set(Gf.Vec3d(1.5,1,21))
    s.GetRootLayer().Save();print(OUTPUT)

if __name__=='__main__':
    build()
