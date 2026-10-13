"""Scenario fault injection only. Pose inference must receive pixels, not CASES."""
CASES={
    'normal':(0.,0.,0.,False),
    'stop_x':(.03,0.,0.,False),
    'lateral_y':(0.,.015,0.,False),
    'yaw':(0.,0.,2.,False),
    'occluded':(0.,0.,0.,True),
    'x_y':(.03,.015,0.,False),
    'x_yaw':(.03,0.,2.,False),
    'y_yaw':(0.,.015,2.,False),
    'x_y_yaw':(.03,.015,2.,False),
    'combined_occluded':(.03,.015,2.,True),
}

def sensor_image(rgb,occluded):
    image=rgb.copy()
    if occluded:
        h,w=image.shape[:2];image[h//4:3*h//4,w//2:3*w//4,:3]=0
    return image
