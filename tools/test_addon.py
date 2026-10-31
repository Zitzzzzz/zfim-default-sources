#!/usr/bin/env python3
import json
import os
import re
import sys
import subprocess
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

class AddonTester:
    def __init__(self, spec_path):
        self.spec_path = spec_path
        with open(spec_path, 'r', encoding='utf-8') as f:
            self.spec = json.load(f)
        self.addon_id = self.spec.get('id')
        self.name = self.spec.get('name')
        self.base = self.spec.get('base')
        self.headers = self.spec.get('headers', {})
        if 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    def test_emulator_injection(self):
        print(f"\n==========================================")
        print(f"Injecting & testing addon '{self.addon_id}' ({self.name})...")
        print(f"==========================================")
        
        # 1. Stop app first
        subprocess.run(['adb', 'shell', 'am', 'force-stop', 'zfim.zfim_flutter'], check=True)
        time.sleep(0.5)

        # 2. Read current FlutterSharedPreferences.xml
        cmd_read = ['adb', 'shell', 'run-as', 'zfim.zfim_flutter', 'cat', '/data/data/zfim.zfim_flutter/shared_prefs/FlutterSharedPreferences.xml']
        res = subprocess.run(cmd_read, capture_output=True, text=True)
        xml_content = res.stdout
        
        root = None
        if '<map>' in xml_content:
            try:
                root = ET.fromstring(xml_content)
            except Exception:
                pass
        if root is None:
            root = ET.Element('map')

        # 3. Find or create custom addons set
        custom_set = None
        for child in list(root):
            if child.tag == 'set' and child.get('name') == 'flutter.zfim_custom_json_addons':
                custom_set = child
                break
            elif child.tag == 'set' and not child.get('name'):
                root.remove(child) # remove broken tag if any

        if custom_set is None:
            custom_set = ET.SubElement(root, 'set', attrib={'name': 'flutter.zfim_custom_json_addons'})

        # Add or replace entry
        addon_entry_json = json.dumps({
            'specJson': json.dumps(self.spec, ensure_ascii=False),
            'repositoryId': 'zfim-default-sources',
            'enabled': True
        }, ensure_ascii=False)

        # Remove previous entry for this id
        new_children = []
        for s in list(custom_set):
            try:
                parsed = json.loads(s.text or '{}')
                spec = json.loads(parsed.get('specJson', '{}'))
                if spec.get('id') != self.addon_id:
                    new_children.append(s)
            except Exception:
                pass
        
        custom_set.clear()
        for c in new_children:
            custom_set.append(c)
        
        new_s = ET.SubElement(custom_set, 'string')
        new_s.text = addon_entry_json

        # Set active addon
        active_elem = None
        for child in list(root):
            if child.get('name') == 'flutter.zfim_active_addon':
                active_elem = child
                break
        if active_elem is None:
            active_elem = ET.SubElement(root, 'string', attrib={'name': 'flutter.zfim_active_addon'})
        active_elem.text = self.addon_id

        # Format XML
        new_xml = '<?xml version=\'1.0\' encoding=\'utf-8\' standalone=\'yes\' ?>\n' + ET.tostring(root, encoding='utf-8').decode('utf-8')
        tmp_local = f"/tmp/prefs_{self.addon_id}.xml"
        with open(tmp_local, 'w', encoding='utf-8') as f:
            f.write(new_xml)

        subprocess.run(['adb', 'push', tmp_local, '/data/local/tmp/new_prefs.xml'], check=True, capture_output=True)
        subprocess.run(['adb', 'shell', 'run-as', 'zfim.zfim_flutter', 'cp', '/data/local/tmp/new_prefs.xml', '/data/data/zfim.zfim_flutter/shared_prefs/FlutterSharedPreferences.xml'], check=True)
        
        # 4. Clear logcat and launch app
        subprocess.run(['adb', 'shell', 'logcat', '-c'])
        subprocess.run(['adb', 'shell', 'monkey', '-p', 'zfim.zfim_flutter', '-c', 'android.intent.category.LAUNCHER', '1'], capture_output=True)
        
        print("App restarted on emulator. Waiting 5s for catalog & UI load...")
        time.sleep(5)

        # 5. Capture logcat
        logcat_res = subprocess.run(['adb', 'logcat', '-d'], capture_output=True, text=True)
        lines = logcat_res.stdout.splitlines()
        relevant_logs = [line for line in lines if any(k in line.lower() for k in ['zfim', 'addon', 'flutter', 'jsonrest', 'jsonscrape', 'error'])]
        
        # 6. Capture screenshot
        screenshot_path = f"/tmp/emulator_{self.addon_id}.png"
        subprocess.run(['adb', 'shell', 'screencap', '-p', '/sdcard/test_screen.png'], capture_output=True)
        subprocess.run(['adb', 'pull', '/sdcard/test_screen.png', screenshot_path], capture_output=True)

        return relevant_logs, screenshot_path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 tester.py <path_to_addon.json>")
        sys.exit(1)
    tester = AddonTester(sys.argv[1])
    logs, screenshot = tester.test_emulator_injection()
    print(f"Screenshot saved to: {screenshot}")
    print("Relevant logs (last 30):")
    for l in logs[-30:]:
        print(l)
