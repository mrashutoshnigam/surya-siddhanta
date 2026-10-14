"""Independent DE440 reconstruction; run from the repository root.

Requires the installed project, numpy and jplephem; reads the existing local kernel.
This audit is not a replacement for the missing published evaluation pipeline.
IAU 2006 angles: Hilton et al. 2006; checked against ERFA pfw06/ecm06.
Delta-T polynomials: https://eclipse.gsfc.nasa.gov/LEcat5/deltatpoly.html
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from jplephem.spk import SPK
from numerics_audit import records, calendar, january_jd, rms, BODIES, ROOT
from suryasiddhanta.ch01_mean_motions import mean_longitude, KALI_EPOCH_JD, SIDEREAL_YEAR_DAYS, julian_day
from suryasiddhanta.ch02_true_places import true_longitude_full, ayanamsha


def wrap(x):
    return (np.asarray(x) + 180) % 360 - 180


def ecliptic(jd, v):
    """ICRS to mean ecliptic/equinox of date, including frame bias.

    Passive rotations Rz(-psi_bar) Rx(phi_bar) Rz(gamma_bar).
    Equatorial precession's final Rx(-eps_A) cancels with Rx(eps_A).
    Numerical polynomials are mathematical coefficients, not copied ERFA code.
    """
    t = (np.asarray(jd) - 2451545.) / 36525
    poly = np.polynomial.polynomial.polyval
    g = np.deg2rad(poly(t, [-.052928, 10.556378, .4932044, -.00031238, -.000002788, .0000000260])/3600)
    p = np.deg2rad(poly(t, [84381.412819, -46.811016, .0511268, .00053289, -.000000440, -.0000000176])/3600)
    s = np.deg2rad(poly(t, [-.041775, 5038.481484, 1.5584175, -.00018522, -.000026452, -.0000000148])/3600)
    x, y, z = v
    x, y = np.cos(g)*x + np.sin(g)*y, -np.sin(g)*x + np.cos(g)*y
    y, z = np.cos(p)*y + np.sin(p)*z, -np.sin(p)*y + np.cos(p)*z
    x, y = np.cos(s)*x - np.sin(s)*y, np.sin(s)*x + np.cos(s)*y
    return np.array([x, y, z])


def delta_t(y):
    """Espenak-Meeus base polynomials for this audit's 1550-2650 window.

    No ELP-specific tidal-acceleration correction is applied to DE440.
    """
    assert np.all((y >= 1550) & (y < 2650))
    result = np.empty_like(y)
    segments = [
        (1550,1600,1000,100,[1574.2,-556.01,71.23472,.319781,-.8503463,-.005050998,.0083572073]),
        (1600,1700,1600,1,[120,-.9808,-.01532,1/7129]),
        (1700,1800,1700,1,[8.83,.1603,-.0059285,.00013336,-1/1174000]),
        (1800,1860,1800,1,[13.72,-.332447,.0068612,.0041116,-.00037436,.0000121272,-.0000001699,.000000000875]),
        (1860,1900,1860,1,[7.62,.5737,-.251754,.01680668,-.0004473624,1/233174]),
        (1900,1920,1900,1,[-2.79,1.494119,-.0598939,.0061966,-.000197]),
        (1920,1941,1920,1,[21.20,.84493,-.076100,.0020936]),
        (1941,1961,1950,1,[29.07,.407,-1/233,1/2547]),
        (1961,1986,1975,1,[45.45,1.067,-1/260,-1/718]),
        (1986,2005,2000,1,[63.86,.3345,-.060374,.0017275,.000651814,.00002373599]),
        (2005,2050,2000,1,[62.92,.32217,.005589]),
    ]
    for lo, hi, origin, scale, coefficients in segments:
        mask = (y >= lo) & (y < hi)
        result[mask] = np.polynomial.polynomial.polyval((y[mask]-origin)/scale, coefficients)
    mask = y >= 2050
    result[mask] = -20 + 32*((y[mask]-1820)/100)**2
    mask = (y >= 2050) & (y < 2150)
    result[mask] -= .5628*(2150-y[mask])
    return result


def references(kernel, tt):
    earth = kernel[0,3].compute(tt) + kernel[3,399].compute(tt)
    ref = {}
    for body, target in [('Sun',10),('Mercury',1),('Venus',2),('Mars',4),('Jupiter',5),('Saturn',6)]:
        xyz = ecliptic(tt, kernel[0,target].compute(tt)-earth)
        ref[body] = np.rad2deg(np.arctan2(xyz[1],xyz[0])) % 360
    mr,mv = kernel[3,301].compute_and_differentiate(tt)
    er,ev = kernel[3,399].compute_and_differentiate(tt)
    r,v = ecliptic(tt,mr-er),ecliptic(tt,mv-ev)
    ref['Moon'] = np.rad2deg(np.arctan2(r[1],r[0])) % 360
    h = np.cross(r.T,v.T).T
    ref['Rahu'] = np.rad2deg(np.arctan2(h[0],-h[1])) % 360
    return ref


def main():
    fr = records('ayanamsha_vs_precession.csv')
    jd = np.array([float(r['jd']) for r in fr])
    years = np.array([float(r['year']) for r in fr])
    frame = np.array([float(r['difference_deg']) for r in fr])
    cy,cm,cd = calendar(jd)
    start = january_jd(cy, jd>=2299160.5)
    end = january_jd(cy+1, jd>=2299160.5)
    # Handle the shortened calendar-switch year in a consistent civil-year scale.
    end = np.where(cy==1582, january_jd(1583,True), end)
    start = np.where(cy==1582, january_jd(1582,False), start)
    civil_year = cy+(jd-start)/(end-start)
    kernel_path = ROOT/'paper/data/kernels/de440.bsp'
    report = {'kernel_sha256':hashlib.sha256(kernel_path.read_bytes()).hexdigest(),
              'epochs':len(jd),'variants':{},'changed_calendar_table_cells':[],
              'great_inequality_fits':{}}
    # Check calendar conversion independently against the existing project helper.
    from suryasiddhanta.ch01_mean_motions import from_julian_day
    assert all(from_julian_day(float(j))[:3] == (int(y),int(m),int(d)) for j,y,m,d in zip(jd,cy,cm,cd))
    aya = np.array([ayanamsha(float(j)) for j in jd])
    ss = {}
    for body in BODIES:
        print('Computing SS',body,flush=True)
        sid = np.array([mean_longitude('Moon_node',float(j)) if body=='Rahu'
                        else true_longitude_full(body,float(j))['true_longitude'] for j in jd])
        ss[body] = (sid+aya)%360
    kernel = SPK.open(str(kernel_path))
    original = {}
    for variant in ['naive','deltat']:
        rows = records('residuals_'+variant+'.csv')
        original[variant] = {b:np.array([float(r['residual_deg']) for r in rows if r['body']==b]) for b in BODIES}
        tt = jd if variant=='naive' else jd-75.7873/360+delta_t(years)/86400
        ref = references(kernel,tt)
        report['variants'][variant] = {}
        for body in BODIES:
            difference = wrap(wrap(ss[body]-ref[body])-original[variant][body])
            report['variants'][variant][body] = {'max_abs_difference_deg':float(np.max(np.abs(difference))),
                                                'rms_difference_deg':rms(difference)}
    corrected_ref = references(kernel,jd-75.7873/360+delta_t(civil_year)/86400)
    ss_tithi = np.floor(((ss['Moon']-ss['Sun'])%360)/12).astype(int)
    ref_tithi = np.floor(((ref['Moon']-ref['Sun'])%360)/12).astype(int)
    report['sampled_tithi_index_disagreements'] = int(np.sum(ss_tithi!=ref_tithi))
    report['sampled_tithi_index_max_circular_difference'] = int(np.max(np.abs((ss_tithi-ref_tithi+15)%30-15)))
    pa = lambda j: np.polynomial.polynomial.polyval((np.asarray(j)-2451545)/36525,
            [0,5028.796195,1.1054348,.00007964,-.000023857,-.0000000383])/3600
    prec = np.array([float(r['true_precession_deg']) for r in fr])
    report['precession_csv_max_difference_deg_by_zero_choice'] = {
        'kali_3600':float(np.max(np.abs(pa(jd)-pa(KALI_EPOCH_JD+3600*SIDEREAL_YEAR_DAYS)-prec))),
        '499_jan_1_julian':float(np.max(np.abs(pa(jd)-pa(julian_day(499,1,1))-prec)))}
    report['turning_point_jd'] = KALI_EPOCH_JD+5400*SIDEREAL_YEAR_DAYS
    report['turning_point_calendar'] = from_julian_day(report['turning_point_jd'])
    old_century = 1550+100*np.floor((years-1550)/100).astype(int)
    new_century = 1550+100*((cy-1550)//100)
    report['corrected_year_deltat_effect_max_deg'] = {}
    for body in BODIES:
        corrected = wrap(ss[body]-corrected_ref[body])
        report['corrected_year_deltat_effect_max_deg'][body] = float(np.max(np.abs(corrected-original['deltat'][body])))
        x = original['deltat'][body]
        for century in sorted(set(old_century)):
            for table,stat in [(2,rms),(3,lambda a:float(np.max(np.abs(a))))]:
                old = stat(x[old_century==century])
                new = stat(x[new_century==century])
                if f'{old:.2f}' != f'{new:.2f}':
                    report['changed_calendar_table_cells'].append({'table':table,'century':int(century),'body':body,'old':f'{old:.2f}','new':f'{new:.2f}'})
    for body in ['Jupiter','Saturn']:
        x = original['deltat'][body]-frame
        linear = np.column_stack([np.ones(len(jd)),years-2100])
        w = 2*np.pi*(years-2100)/883
        harmonic = np.column_stack([np.sin(w),np.cos(w)])
        beta = np.linalg.lstsq(linear,x,rcond=None)[0]
        gamma = np.linalg.lstsq(harmonic,x-linear@beta,rcond=None)[0]
        sequential = np.linalg.lstsq(linear,x-harmonic@gamma,rcond=None)[0]
        joint = np.linalg.lstsq(np.column_stack([linear,harmonic]),x,rcond=None)[0]
        report['great_inequality_fits'][body] = {
            'sequential_drift_arcsec_yr':float(sequential[1]*3600),
            'sequential_amplitude_arcmin':float(np.linalg.norm(gamma)*60),
            'joint_drift_arcsec_yr':float(joint[1]*3600),
            'joint_amplitude_arcmin':float(np.linalg.norm(joint[2:])*60)}
    report['ayanamsha_csv_max_difference_deg'] = float(np.max(np.abs(aya-np.array([float(r['ss_ayanamsha_deg']) for r in fr]))))
    kernel.close()
    dest = Path(__file__).with_name('kernel_results.json')
    dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
