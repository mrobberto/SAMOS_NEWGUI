;THIS PROGRAM CALCULATES THE BRIGHTNESS OF THE SKY IN THE VISIBLE 
;SEEN FROM A SPECTROGRAPH, ON THE BASES OF THE ESO UVES SPECTRA

pro myreadfits,file,wavel,flux,header
fits_read, file, flux, header
crpos=where(strmid(header,0,6) eq "CRVAL1")
cr=strmid(header[crpos[0]],9,60)+0.
cdeltpos=where(strmid(header,0,6) eq "CDELT1")
cdelt=strmid(header[cdeltpos[0]],9,60)+0.
wavel=findgen(n_elements(flux))*cdelt+cr
end

pro Sky_ground, wl, fl
myreadfits,'~/Dropbox/2013/2013.SOAR/ETC/eso/UVES_sky_all/fluxed_sky_346.fits',wavel0,flux0; spectru is stored in log units
myreadfits,'~/Dropbox/2013/2013.SOAR/ETC/eso/UVES_sky_all/fluxed_sky_437.fits',wavel1,flux1
myreadfits,'~/Dropbox/2013/2013.SOAR/ETC/eso/UVES_sky_all/fluxed_sky_564U.fits',wavel3,flux3  ;switch short/long
myreadfits,'~/Dropbox/2013/2013.SOAR/ETC/eso/UVES_sky_all/fluxed_sky_580L.fits',wavel2,flux2  ;switch short/long
myreadfits,'~/Dropbox/2013/2013.SOAR/ETC/eso/UVES_sky_all/fluxed_sky_800U.fits',wavel4,flux4
myreadfits,'~/Dropbox/2013/2013.SOAR/ETC/eso/UVES_sky_all/fluxed_sky_860L.fits',wavel5,flux5
myreadfits,'~/Dropbox/2013/2013.SOAR/ETC/eso/UVES_sky_all/fluxed_sky_860U.fits',wavel6,flux6
plot,[3000,11000],[-2,20],/nodata
;stop
;oplot,wavel0,flux0
;oplot,wavel1,flux1
;oplot,wavel2,flux2
;oplot,wavel3,flux3
;oplot,wavel4,flux4
;oplot,wavel5,flux5
;oplot,wavel6,flux6

;sort the wl and create the new spectrum
wavel=[wavel0,wavel1,wavel2,wavel3,wavel4,wavel5,wavel5[45276]+indgen(75),wavel6]
;help,wavel
;WAVEL           FLOAT     = Array[203170]
flux=[flux0,flux1,flux2,flux3,flux4,flux5,replicate(0,75),flux6]  ;spectra are on a logarithmic scale
help,flux
;FLUX            FLOAT     = Array[203170]
iwl=sort(wavel)
;
wl=wavel[iwl]>0
fl=flux[iwl]>0
;
;remove a few multiple points
uwl=uniq(wl)
wl=wl[uwl]
fl=(fl[uwl]) * 1E-16  ;units are 1E-16 erg/s/A/cm2/arcsec, see www.eso.org/observing/dfo/quality/UVES/img/sky/plot_INT.gif
;
writecol,'~/Dropbox/2013/2013.SOAR/ETC/UVES_Fluxed_SkyALL.txt',wl,fl;,FMT='(F12.4,E12.4)'
;
end

                                                                                                                                                                              
;cut the range of wavelengths seen by SAM
pro work
Sky_ground, wl, fl
lambda_min=6000.
lambda_max=10000.
i_min = WHERE(ABS(wl-lambda_min) EQ MIN(ABS(wl-lambda_min)))
i_max = WHERE(ABS(wl-lambda_max) EQ MIN(ABS(wl-lambda_max)))
wl1=wl[i_min:i_max]
fl1=fl[i_min:i_max]
plot,wl1,fl1,yrange=[-1,100]
help,wl1
;WL1             FLOAT     = Array[95942]
;
;rebin spectrum at resolution R=2000
wl_SAMOS = congrid(wl1,2000,/CENTER,/CUBIC)
fl_SAMOS = congrid(fl1,2000,/CENTER,/CUBIC)
;
stop
for i=0,1999 do begin & $
   lambda_min=6000+i*2 & $ 
   lambda_max=6000+(i+1)*2 & $
   i_min = (WHERE(ABS(wl-lambda_min) EQ MIN(ABS(wl-lambda_min))))[0] & $
   i_max = (WHERE(ABS(wl-lambda_max) EQ MIN(ABS(wl-lambda_max))))[0] & $
   wl_samos[i]=avg(wl[i_min:i_max-1]) & $
   Fl_samos[i]=integrate_spectrum(wl[i_min:i_max-1],fl[i_min:i_max-1]) & $
;   print,wl_samos[i],Fl_samos[i],integrate_spectrum(wl[i_min:i_max-1],fl[i_min:i_max-1])
;   stop
;   print,[i,lambda_min,lambda_max,wl_samos[i],Fl_samos[i]] & $
endfor
stop
writecol,'~/Dropbox/2013/2013.SOAR/ETC/Ic_SAMOS_Sky.txt',wl_samos,fl_samos,FMT='(F12.4,E12.4)'
;
;calibration
;Ic band
Ic0 = 7900.
dIc = 1600.
wlIcMin = Ic0 - dIc/2.   & wlIcMax = Ic0 + dIc/2.
Ic_min = (WHERE(ABS(wl_samos-wlIcMin) EQ MIN(ABS(wl_samos-wlIcMin))))[0]
Ic_max = (WHERE(ABS(wl_samos-wlIcMax) EQ MIN(ABS(wl_samos-wlIcMax))))[0] 
wl_Ic = wl_samos[Ic_min:Ic_max]
fl_Ic = fl_samos[Ic_min:Ic_max]
;SkyCounts_Ic=integrate_spectrum(wl_Ic,fl_Ic)

;from here has to be revised...
mag_I=19.9
ZP_I = 2.5*alog10(SkyCounts_Ic)+mag_I 
;print,ZP_I
;      29.6378
iBad = WHERE(fl_Ic gt 50, Nbad)
print,Nbad
;          33
iGood = WHERE(fl_Ic lt 50)
print,-2.5*alog10(total(fl_Ic[iGood]))+ZP_I
;      20.3984
;
;SUMMARY: removing the 33 brightest lines from the I band spectrum, at resolution 2000,
;reduces the integrated sky background by about 0.5mag.
;
;The sky floor calcultated betwen 8200 and 8300A is
i8200s = (WHERE(ABS(wl_samos-8200) EQ MIN(ABS(wl_samos-8200))))[0]
i8300s = (WHERE(ABS(wl_samos-8300) EQ MIN(ABS(wl_samos-8300))))[0] 
print,-2.5*alog10(total(fl_samos[i8200s:i8300s]))+ZP_I
;      22.4405 ;with SAMOS
;The sky floor calcultated betwen 8200 and 8300A is
i8200 = (WHERE(ABS(wl1-8200) EQ MIN(ABS(wl1-8200))))[0]
i8300 = (WHERE(ABS(wl1-8300) EQ MIN(ABS(wl1-8300))))[0] 
print,-2.5*alog10(total(fl[i8200:i8300]))+ZP_I
end
;      23.373  ; with UVES 