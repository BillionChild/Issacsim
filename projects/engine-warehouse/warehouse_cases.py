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

# Engine-only offsets from its normal pallet seat: mm XYZ, degrees roll/pitch/yaw.
# Pallet remains in its nominal pose. Pose faults never change part inspection.
ENGINE_CASES={
    'engine_normal':(0.,0.,0.,0.,0.,0.),
    'engine_shift':(30.,15.,0.,0.,0.,2.),
    'engine_high':(0.,0.,20.,0.,0.,0.),
    'engine_roll':(0.,0.,15.,2.,0.,0.),
    'engine_pitch':(0.,0.,15.,0.,-2.,0.),
    'engine_combined':(20.,-12.,20.,1.5,-1.,2.),
    'engine_combined_occluded':(20.,-12.,20.,1.5,-1.,2.),
}
CASES.update({name:(0.,0.,0.,name.endswith('_occluded')) for name in ENGINE_CASES})

def sensor_image(rgb,occluded):
    image=rgb.copy()
    if occluded:
        h,w=image.shape[:2];image[h//4:3*h//4,w//2:3*w//4,:3]=0
    return image
