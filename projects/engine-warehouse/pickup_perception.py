"""Learned RGB pose regression. Inference has no USD/case/ground-truth access."""
from pathlib import Path
import numpy as np

MODEL=Path(__file__).resolve().parents[2]/'outputs/pickup-perception/model.npz'

def features(rgb,side=64):
    from PIL import Image
    crop=np.asarray(rgb)[160:464,80:432,:3]
    return np.asarray(Image.fromarray(crop.astype('uint8')).convert('L').resize((side,side)),dtype=float).ravel()/255.

def train(images,poses,path,calibration,feature_side=64,kernel_sigma=None):
    x=np.stack([features(im,feature_side) for im in images]);y=np.asarray(poses)
    mean=x.mean(0);ym=y.mean(0);xc=x-mean
    if kernel_sigma is not None:
        norms=np.sum(x*x,axis=1)
        distances=np.maximum((norms[:,None]+norms[None,:]-2*x@x.T)/x.shape[1],0)
        kernel=np.exp(-distances/(2*kernel_sigma**2))
        alpha=np.linalg.solve(kernel+.01*np.eye(len(x)),y-ym)
        np.savez_compressed(path,ym=ym,alpha=alpha,train=x,kernel_sigma=kernel_sigma,feature_side=feature_side,**calibration)
        return
    # Dual ridge avoids a large pixel x pixel system. Labels: mm, mm, degrees.
    dual=np.linalg.solve(xc@xc.T+.03*np.eye(len(x)),y-ym)
    weights=xc.T@dual
    np.savez_compressed(path,mean=mean,ym=ym,weights=weights,train=x,feature_side=feature_side,**calibration)

class Predictor:
    def __init__(self,path=MODEL):
        with np.load(path) as data:self.data={k:data[k] for k in data.files}
    def predict(self,rgb):
        rgb=np.asarray(rgb)
        if rgb.shape[:2]!=(512,512):raise ValueError('Expected calibrated 512x512 image')
        crop=rgb[160:464,80:432,:3]
        black=float(np.mean(np.max(crop,axis=2)<3))
        d=self.data;x=features(rgb,int(d.get('feature_side',64)))
        distances=np.mean((d['train']-x)**2,axis=1)
        novelty=float(np.sqrt(np.min(distances)))
        if 'kernel_sigma' in d:
            pose=np.exp(-distances/(2*float(d['kernel_sigma'])**2))@d['alpha']+d['ym']
        else:pose=(x-d['mean'])@d['weights']+d['ym']
        reason='ESTIMATE_ONLY'
        if black>.04:reason='HOLD: missing / dark image region'
        elif novelty>.075:reason='HOLD: image differs from training'
        elif np.any(np.abs(pose)>[40,25,3]):reason='HOLD: outside training range'
        return dict(pose=pose.tolist(),accepted=reason=='ESTIMATE_ONLY',reason=reason,
                    image_distance=novelty,black_fraction=black)

def annotated(rgb,result,calibration,path):
    from PIL import Image,ImageDraw
    im=Image.fromarray(np.asarray(rgb)[:,:,:3].astype('uint8'));draw=ImageDraw.Draw(im)
    def polygon(dx,dy,yaw):
        theta=np.radians(yaw);rot=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        points=[]
        for xy in ((-.4,-.4),(.4,-.4),(.4,.4),(-.4,.4)):
            q=np.array(xy)@rot.T+[dx/1000.,-2.2+dy/1000.]
            p=np.array([q[0],q[1],.72,1.])@calibration['world_to_camera']
            f=float(calibration['focal_pixels']);points.append((256+f*p[0]/-p[2],256-f*p[1]/-p[2]))
        draw.line(points+[points[0]],fill=(40,255,100) if dx==dy==yaw==0 else (255,170,30),width=3)
    polygon(0,0,0)
    if result['accepted']:polygon(*result['pose'])
    draw.rectangle((0,0,512,62),fill=(20,24,30))
    draw.text((10,8),'GREEN: nominal pallet | ORANGE: learned estimate',fill='white')
    dx,dy,yaw=result['pose']
    draw.text((10,25),f'X {dx:+.1f} mm   Y {dy:+.1f} mm   yaw {yaw:+.2f} deg' if result['accepted'] else 'Pose withheld: observation cannot be trusted',fill='white')
    draw.text((10,43),result['reason']+' | observation snapshot',fill='white')
    im.save(path)
