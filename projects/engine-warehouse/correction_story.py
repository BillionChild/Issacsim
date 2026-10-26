"""Presentation from inference and commanded frames; never scenario truth."""
from pathlib import Path
from fanuc_kinematics import np, fk, Rotation

def story(model):
    result=model.vision_result or {};phase=model.robot_frame.phase
    check=next((v for v in model.pickup_checks if v['engine']=='E1'),None)
    if model.fault:return dict(title='HOLD - no safe continuation',detail=model.fault,verified=False)
    if check:return dict(title='6 / VERIFIED AT RACK',detail=f"Measured seat error: {check['seat_error_m']*1000:.2f} mm. Pickup and storage completed.",verified=True)
    if not result.get('accepted'):return dict(title='1 / OBSERVE ENGINE',detail='Waiting for a valid camera estimate. No correction target yet.',verified=False)
    if phase in ('CLOSE_JAWS','ATTACH_ENGINE_KINEMATIC'):
        title='3 / CLOSE AND CHECK GRIP';detail='Close at the estimated engine pose. Check support alignment before attachment.'
    elif phase in ('LIFT_ENGINE_POSE','LIFT_ENGINE'):
        title='4 / LIFT IN THE CURRENT POSE';detail='Keep the captured engine attitude while lifting clear of the pallet.'
    elif phase in ('LEVEL_ENGINE_IN_AIR','VISION_REJOIN'):
        title='5 / LEVEL ABOVE THE CONVEYOR';detail='Rotate the lifted engine back to the nominal storage attitude.'
    elif model.engines['E1']['owner']!='pallet':
        title='5 / MOVE TO STORAGE';detail='Follow the rack route. Success is shown only after the seating check.'
    else:
        title='2 / CORRECT THE GRIPPER APPROACH';detail='Move the gripper to the estimated engine pose. The engine stays on the pallet.'
    return dict(title=title,detail=detail,verified=False)

def command_delta(model):
    if not (model.vision_result or {}).get('accepted') or not model.guided_frames:return None
    nominal=next(f for f in model.motions['inbound','A'] if f.owner=='gripper')
    corrected=next(f for f in model.guided_frames if f.owner=='gripper')
    p0,r0=fk(nominal.q,(0,0,0));p1,r1=fk(corrected.q,(0,0,0))
    return np.r_[(p1-p0)*1000,Rotation.from_matrix(r1@r0.T).as_euler('xyz',degrees=True)].tolist()

def comparison_image(result,path):
    """Frozen observation + explicitly exaggerated diagrams, not a new sensor input."""
    from PIL import Image,ImageDraw,ImageFont
    import math
    im=Image.new('RGB',(1100,650),'#161e29');d=ImageDraw.Draw(im)
    def font(n):
        try:return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
        except OSError:return ImageFont.load_default()
    def text(x,y,s,color='#eeeeee',size=22):d.text((x,y),s,font=font(size),fill=color)
    green='#65dd9a';orange='#ffba58'
    text(20,14,'CAMERA OBSERVATION',size=26);text(560,14,'WHAT IS DIFFERENT?',size=26)
    evidence=result.get('evidence')
    if evidence and Path(evidence).exists():
        photo=Image.open(evidence).convert('RGB');im.paste(photo.resize((500,500)),(20,60))
    text(20,572,'Captured image - not live video',size=20)
    if not result.get('accepted'):
        text(560,95,'NO ACCEPTED ESTIMATE',orange,26);text(560,140,'No correction is drawn.',size=22)
    else:
        pose=result.get('pose6')
        if pose is None:
            x,y,yaw=result['pose'];pose=[x,y,0,0,0,yaw]
        x,y,z,roll,pitch,yaw=pose
        text(560,55,'GREEN: normal reference',green,22);text(560,86,'ORANGE: camera estimate',orange,22)
        text(560,121,'TOP VIEW | X / Y / yaw',size=23)
        def outline(cx,cy,angle,color,w=80,h=35):
            a=math.radians(angle);points=[]
            for u,v in [(-w,-h),(w,-h),(w,h),(-w,h),(-w,-h)]:points.append((cx+u*math.cos(a)-v*math.sin(a),cy+u*math.sin(a)+v*math.cos(a)))
            d.line(points,fill=color,width=4)
        outline(780,250,0,green)
        # Diagram only: 2px/mm translations and 5x angles. No world geometry altered.
        outline(780+x*2,250-y*2,-yaw*5,orange)
        d.line([(780,250),(780+x*2,250-y*2)],fill=orange,width=3)
        text(560,365,f'X {x:+.1f} mm   Y {y:+.1f} mm   Z {z:+.1f} mm',size=23)
        text(560,403,f'Yaw {yaw:+.2f} deg',orange,23)
        for cx,angle,label in [(680,roll,'ROLL'),(940,pitch,'PITCH')]:
            d.line([(cx-80,492),(cx+80,492)],fill=green,width=4)
            a=math.radians(angle*5);dy=-z*2
            d.line([(cx-80*math.cos(a),492+dy+80*math.sin(a)),(cx+80*math.cos(a),492+dy-80*math.sin(a))],fill=orange,width=4)
            text(cx-95,535,f'{label} {angle:+.2f} deg',orange,22)
        text(560,585,'Diagram: angles x5; offsets enlarged.',size=19)
        text(560,611,'Numbers are the actual estimated values.',size=19)
    im.save(path);return str(path)
