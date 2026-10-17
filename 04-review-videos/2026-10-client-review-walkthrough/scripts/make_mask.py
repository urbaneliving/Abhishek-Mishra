import subprocess, numpy as np, cv2
W,H=1272,720; X1,Y1,X2,Y2=0,0,420,130
fr=[]
for t in np.linspace(3,315,80):
    b=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i','raw/original.mp4','-frames:v','1','-f','rawvideo','-pix_fmt','bgr24','-'],capture_output=True).stdout
    fr.append(np.frombuffer(b,np.uint8).reshape(H,W,3)[Y1:Y2,X1:X2].astype(np.float32))
st=np.stack(fr); sd=st.std(0).mean(2); med=np.median(st,0)
mask=(sd<14).astype(np.uint8)*255
# keep only components that touch the logo box
n,lab,stats,_=cv2.connectedComponentsWithStats(mask)
keep=np.zeros_like(mask)
for i in range(1,n):
    x,y,w,h,a=stats[i]
    if 3<=x<=380 and 15<=y<=110 and a>4: keep[lab==i]=255
keep=cv2.dilate(keep,np.ones((5,5),np.uint8),2)
cv2.imwrite('work/logo_mask.png',keep); cv2.imwrite('work/logo_median.png',med.astype(np.uint8))
ys,xs=np.nonzero(keep); print('bbox',xs.min(),ys.min(),xs.max(),ys.max())
