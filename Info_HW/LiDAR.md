# LiDAR Information
- Model : OS1-64
- Manufacturer : OUSTER
- Maximum Range : 100m
- Minimum Range : 0.3m
- Vertical Resolution : 64 channels
- FoV (Field of View) : Vertical 45°, Horizontal 360°
- [DataSheet](./LiDAR/datasheet-rev06-v2p3-os1.pdf)
- [Software User Manual](./LiDAR/software-user-manual-v2p0.pdf)

## Setup
The links below will help the initial setup of Ouster LiDAR.

[Introduction to Ouster Digital Lidar](https://static.ouster.dev/sensor-docs/index.html?highlight=visualizer)  
[Connecting to Sensor](https://static.ouster.dev/sensor-docs/image_route1/image_route2/connecting/connecting-to-sensors.html#connecting-to-sensor)
- By following this, you can know how to set the network configuration between LiDAR and host machine.
- In the middle of [Connecting to Sensor](https://static.ouster.dev/sensor-docs/image_route1/image_route2/connecting/connecting-to-sensors.html#connecting-to-sensor), it says "*May be required to deactivate the firewall to connect with the sensor and access sensor data.*" and for this, you need to open a UDP port to get LiDAR point-cloud data.
- [How to open a UDP port](https://www.cyberciti.biz/faq/how-to-open-firewall-port-on-ubuntu-linux-12-04-14-04-lts/)
- You can find the UDP port in `Configuration` tab at Web Interface in [Connecting to Sensor](https://static.ouster.dev/sensor-docs/image_route1/image_route2/connecting/connecting-to-sensors.html#connecting-to-sensor).