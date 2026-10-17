# Remove old Space Interio logo (inpaint), upscale to 1080p, place Urbane Living logo.
import subprocess, sys, numpy as np, cv2
src, dst = sys.argv[1], sys.argv[2]
extra = sys.argv[3:]   # e.g. -ss 10 -t 5 for tests
W,H=1272,720
mask=cv2.imread('work/mask_full.png',0)
ys,xs=np.nonzero(mask); x1,y1,x2,y2=max(xs.min()-20,0),max(ys.min()-20,0),xs.max()+20,ys.max()+20
sub=mask[y1:y2,x1:x2]
dec=subprocess.Popen(['ffmpeg','-v','error',*extra,'-i',src,'-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
vf=("[0:v]deblock=filter=strong:block=8,hqdn3d=2:1.5:4:4,scale=1920:1086:flags=lanczos,crop=1920:1080,unsharp=5:5:0.9:3:3:0.4,eq=contrast=1.04:saturation=1.08:gamma=1.02[v];"
    "[v][2:v]overlay=4:6[out]")
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','30','-i','-',
    *extra,'-i',src,'-i','work/logo_overlay.png','-filter_complex',vf,'-map','[out]','-map','1:a?',
    '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-af','loudnorm=I=-14:TP=-1.5:LRA=11',
    '-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',dst],stdin=subprocess.PIPE)
n=0
while True:
    b=dec.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    f=np.frombuffer(b,np.uint8).reshape(H,W,3).copy()
    roi=f[y1:y2,x1:x2]
    fill=cv2.inpaint(roi,sub,9,cv2.INPAINT_NS)
    fill=np.where(sub[...,None]>0,cv2.GaussianBlur(fill,(9,9),0),fill)
    g=cv2.cvtColor(cv2.cvtColor(fill,cv2.COLOR_BGR2GRAY),cv2.COLOR_GRAY2BGR)
    k=cv2.GaussianBlur(sub,(31,31),0)[...,None]/255.0*0.7
    fill=(fill*(1-k)+g*k).astype(np.uint8)
    f[y1:y2,x1:x2]=fill
    enc.stdin.write(f.tobytes()); n+=1
enc.stdin.close(); enc.wait(); print('frames',n)
