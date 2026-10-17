# Remove old Space Interio logo, put a frosted-blur panel only behind the new logo,
# upscale to 1080p (no global filters, rest of the picture untouched), overlay Urbane Living logo.
import subprocess, sys, numpy as np, cv2
src, dst = sys.argv[1], sys.argv[2]
extra = sys.argv[3:]   # e.g. -ss 10 -t 5 for tests
W,H=1272,720
mask=cv2.imread('work/mask_full.png',0)
ys,xs=np.nonzero(mask); x1,y1,x2,y2=max(xs.min()-20,0),max(ys.min()-20,0),xs.max()+20,ys.max()+20
sub=mask[y1:y2,x1:x2]
# frosted panel (720p coords), rounded corners, soft edge
PX1,PY1,PX2,PY2,R=9,12,407,154,16
pm=np.zeros((H,W),np.uint8)
cv2.rectangle(pm,(PX1+R,PY1),(PX2-R,PY2),255,-1); cv2.rectangle(pm,(PX1,PY1+R),(PX2,PY2-R),255,-1)
for cx,cy in [(PX1+R,PY1+R),(PX2-R,PY1+R),(PX1+R,PY2-R),(PX2-R,PY2-R)]: cv2.circle(pm,(cx,cy),R,255,-1,cv2.LINE_AA)
pm=cv2.GaussianBlur(pm,(5,5),0)[...,None]/255.0
bx1,by1,bx2,by2=0,0,PX2+60,PY2+60
dec=subprocess.Popen(['ffmpeg','-v','error',*extra,'-i',src,'-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
vf="[0:v]scale=1920:1086:flags=lanczos,crop=1920:1080[v];[v][2:v]overlay=89:39[out]"
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','30','-i','-',
    *extra,'-i',src,'-i','work/logo_plain.png','-filter_complex',vf,'-map','[out]','-map','1:a?',
    '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',
    '-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',dst],stdin=subprocess.PIPE)
n=0
while True:
    b=dec.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    f=np.frombuffer(b,np.uint8).reshape(H,W,3).copy()
    f[y1:y2,x1:x2]=cv2.inpaint(f[y1:y2,x1:x2],sub,9,cv2.INPAINT_NS)
    reg=f[by1:by2,bx1:bx2].astype(np.float32)
    frost=cv2.GaussianBlur(reg,(0,0),18)*0.8+255*0.2          # blur + light white tint
    m=pm[by1:by2,bx1:bx2]
    f[by1:by2,bx1:bx2]=(reg*(1-m)+frost*m).astype(np.uint8)
    enc.stdin.write(f.tobytes()); n+=1
enc.stdin.close(); enc.wait(); print('frames',n)
