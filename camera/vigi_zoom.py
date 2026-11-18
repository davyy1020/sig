import sys
import os
import urllib.request
import ssl
import base64
import hashlib
import time

ctx = ssl._create_unverified_context()

class VigiOpticalZoomController:
    def __init__(self, ip="192.168.136.108", port=2020, user="admin", password="sigma123"):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.service_url = f"http://{ip}:{port}/onvif/service"
        self.profile_token = "profile_1"

    def _build_ws_security_header(self):
        created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        nonce_bytes = os.urandom(16)
        nonce_b64 = base64.b64encode(nonce_bytes).decode('ascii')
        
        sha1 = hashlib.sha1()
        sha1.update(nonce_bytes + created.encode('ascii') + self.password.encode('ascii'))
        digest_b64 = base64.b64encode(sha1.digest()).decode('ascii')
        
        return f"""
        <s:Header xmlns:s="http://www.w3.org/2003/05/soap-envelope">
          <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
                         xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
            <wsse:UsernameToken>
              <wsse:Username>{self.user}</wsse:Username>
              <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest">{digest_b64}</wsse:Password>
              <wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">{nonce_b64}</wsse:Nonce>
              <wsu:Created>{created}</wsu:Created>
            </wsse:UsernameToken>
          </wsse:Security>
        </s:Header>
        """

    def _send_soap(self, body):
        hdr = self._build_ws_security_header()
        soap = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
            xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"
            xmlns:tt="http://www.onvif.org/ver10/schema">
  {hdr}
  <s:Body>
    {body}
  </s:Body>
</s:Envelope>"""
        req = urllib.request.Request(self.service_url, data=soap.encode('utf-8'))
        req.add_header('Content-Type', 'application/soap+xml; charset=utf-8')
        try:
            res = urllib.request.urlopen(req, context=ctx, timeout=3)
            return True, res.read().decode('utf-8')
        except Exception as e:
            err_msg = str(e)
            if hasattr(e, 'read'):
                try: err_msg += " " + e.read().decode('utf-8', errors='ignore')
                except: pass
            return False, err_msg

    def zoom_step(self, direction="in", step=0.15):
        """RelativeMove optical zoom: direction='in' (tele) or 'out' (wide)."""
        val = abs(float(step))
        if direction.lower() in ("out", "wide", "-"):
            val = -val
        val = max(-1.0, min(1.0, val))
        body = f"""
        <tptz:RelativeMove xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">
          <tptz:ProfileToken>{self.profile_token}</tptz:ProfileToken>
          <tptz:Translation>
            <tt:Zoom x="{val:.2f}"/>
          </tptz:Translation>
        </tptz:RelativeMove>
        """
        ok, res = self._send_soap(body)
        return ok, res

    def zoom_absolute(self, position=0.0):
        """AbsoluteMove optical zoom: position from 0.0 (1x Wide) to 1.0 (Max Tele)."""
        pos = max(0.0, min(1.0, float(position)))
        body = f"""
        <tptz:AbsoluteMove xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">
          <tptz:ProfileToken>{self.profile_token}</tptz:ProfileToken>
          <tptz:Position>
            <tt:Zoom x="{pos:.2f}"/>
          </tptz:Position>
          <tptz:Speed>
            <tt:Zoom x="1.0"/>
          </tptz:Speed>
        </tptz:AbsoluteMove>
        """
        ok, res = self._send_soap(body)
        return ok, res

    def zoom_stop(self):
        body = f"""
        <tptz:Stop xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">
          <tptz:ProfileToken>{self.profile_token}</tptz:ProfileToken>
          <tptz:PanTilt>false</tptz:PanTilt>
          <tptz:Zoom>true</tptz:Zoom>
        </tptz:Stop>
        """
        ok, res = self._send_soap(body)
        return ok, res

if __name__ == "__main__":
    controller = VigiOpticalZoomController()
    print("Testing Zoom In Step...")
    ok, res = controller.zoom_step("in", 0.15)
    print("Zoom In Result:", ok)
    time.sleep(1)
    print("Testing Zoom Out Step...")
    ok, res = controller.zoom_step("out", 0.15)
    print("Zoom Out Result:", ok)
