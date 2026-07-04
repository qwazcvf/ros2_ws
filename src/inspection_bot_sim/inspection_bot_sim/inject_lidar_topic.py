#!/usr/bin/env python3
"""Inject /scan topic and frame_id into a Gazebo SDF lidar sensor."""
import sys
import xml.etree.ElementTree as ET

def inject(sdf_path, out_path):
    ET.register_namespace('', 'http://sdformat.org/sdf/1.6')
    tree = ET.parse(sdf_path)
    root = tree.getroot()

    for sensor in root.iter('sensor'):
        name = sensor.get('name', '')
        stype = sensor.get('type', '')
        if 'lidar' in name or 'lidar' in stype or 'gpu_lidar' in stype:
            # Add topic
            topic_el = sensor.find('topic')
            if topic_el is None:
                topic_el = ET.SubElement(sensor, 'topic')
            topic_el.text = '/scan'

            # Add frame_id (Ignition uses <frame_id> or <ignition_frame_id>)
            frame_el = sensor.find('frame_id')
            if frame_el is None:
                frame_el = sensor.find('ignition_frame_id')
            if frame_el is None:
                frame_el = ET.SubElement(sensor, 'frame_id')
            frame_el.text = 'lidar_link'

            print(f"Injected topic=/scan frame_id=lidar_link into sensor '{name}'")

    tree.write(out_path, xml_declaration=True, encoding='UTF-8')
    print(f"Written: {out_path}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.sdf> <output.sdf>")
        sys.exit(1)
    inject(sys.argv[1], sys.argv[2])
