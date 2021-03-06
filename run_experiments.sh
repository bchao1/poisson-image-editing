# Seamless cloning
time python3 seamless_cloning.py --data_dir data/test1 --gradient_mixing_mode alpha --gradient_mixing_alpha 1.0
time python3 seamless_cloning.py --data_dir data/test2 
time python3 seamless_cloning.py --data_dir data/test3 
time python3 seamless_cloning.py --data_dir data/test4 

# Seamless tiling
time python3 seamless_tiling.py --data_dir data/texture1 --scale 0.5
time python3 seamless_tiling.py --data_dir data/texture2 --scale 0.5
time python3 seamless_tiling.py --data_dir data/texture3 --scale 0.5

# Texture flattening
time python3 texture_flattening.py --data_dir data/test5 \
    --edge_dilation_kernel 3 \
    --canny_threshold 25 100

# Local illumination change
time python3 local_illumination_change.py --data_dir data/illum1

# Local color change
time python3 local_color_change.py --data_dir data/color1 --mode color_change --change_hue 60
time python3 local_color_change.py --data_dir data/color1 --mode color_change --change_hue 120
time python3 local_color_change.py --data_dir data/color1 --mode gray_background


# Use multigrid solver to edit a 1080p image
time python3 seamless_cloning.py --data_dir data/test2 --scale 9.6 --solver multigrid
