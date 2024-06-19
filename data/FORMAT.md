For each timestep:
```
- timestamp         (1,)        'uint64'        8 byte

- image_timestamp   (1,)        'uint64'        8 byte
- color_image       (480,640,3) 'uint8'         (480*640*3) * 1 byte = 912,600 byte
- depth_image       (480,640)   'uint16'        (480*640) * 2 byte = 614,400 byte

- pose_timestamp    (1,)        'uint64'        8 byte
- pose_value        (4,4)       'float64'       (4*4) * 8 byte = 128 byte
- pose_confidence   (1,)        'uint8'         1 byte

- trigger_timestamp (1,)        'uint64'        8 byte
- trigger_state     (1,)        'uint8'         1 byte

- gripper_timestamp (1,)        'uint64'        8 byte
- gripper_state     (1,)        'uint8'         1 byte

5*8+3*1+128+614,400+912,600 = 1,527,171 byte

1,527,171 byte / 1,048,576 bytes/MB = 1.456423 MB
```