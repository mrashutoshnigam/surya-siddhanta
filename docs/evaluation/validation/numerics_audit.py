"""Independent CSV audit of the evaluation manuscript.

Run from the repository root:
    python docs/evaluation/validation/numerics_audit.py

Reads source artifacts only; writes numerics_results.json beside this script.
Requires NumPy. Does not use the absent evaluation package or a DE kernel.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'docs' / 'evaluation'
BODIES = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu']

def records(name):
    with (DATA / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def rms(x):
    return float(np.sqrt(np.mean(np.square(x))))

def calendar(jd):
    """Meeus JD-to-calendar algorithm, Julian before 1582-10-15."""
    z = np.floor(jd + .5)
    f = jd + .5 - z
    alpha = np.floor((z - 1867216.25) / 36524.25)
    a = np.where(z < 2299161, z, z + 1 + alpha - np.floor(alpha / 4))
    b = a + 1524
    c = np.floor((b - 122.1) / 365.25)
    d = np.floor(365.25 * c)
    e = np.floor((b - d) / 30.6001)
    day = b - d - np.floor(30.6001 * e) + f
    month = np.where(e < 14, e - 1, e - 13)
    year = np.where(month > 2, c - 4716, c - 4715)
    return year.astype(int), month.astype(int), day

def january_jd(year, gregorian=True):
    y = np.asarray(year) - 1
    a = np.floor(y / 100)
    b = np.where(gregorian, 2 - a + np.floor(a / 4), 0)
    return np.floor(365.25 * (y + 4716)) + np.floor(30.6001 * 14) + 1 + b - 1524.5

def summarize(x):
    return {'n':len(x), 'mean':float(np.mean(x)), 'rms':rms(x),
            'max_abs':float(np.max(np.abs(x))), 'max_signed':float(x[np.argmax(np.abs(x))])}

def main():
    report = {'inputs':{}, 'grid':{}, 'table_checks':{}, 'table4':{}, 'table5':{}, 'discussion':{}}
    filenames = ['residuals_naive.csv','residuals_deltat.csv','century_naive.csv',
                 'century_deltat.csv','ayanamsha_vs_precession.csv']
    for name in filenames:
        report['inputs'][name] = {'sha256':hashlib.sha256((DATA/name).read_bytes()).hexdigest()}
    fr = records('ayanamsha_vs_precession.csv')
    jd = np.array([float(r['jd']) for r in fr])
    year = np.array([float(r['year']) for r in fr])
    frame = np.array([float(r['difference_deg']) for r in fr])
    aya = np.array([float(r['ss_ayanamsha_deg']) for r in fr])
    prec = np.array([float(r['true_precession_deg']) for r in fr])
    data = {}
    alignment = []
    for variant in ['naive','deltat']:
        rows = records('residuals_'+variant+'.csv')
        assert len(rows) == len(jd)*8
        assert set(r['body'] for r in rows) == set(BODIES)
        data[variant] = {}
        for body in BODIES:
            rs = [r for r in rows if r['body'] == body]
            rjd = np.array([float(r['jd']) for r in rs])
            ry = np.array([float(r['year']) for r in rs])
            assert np.array_equal(rjd, jd), (variant,body,'jd mismatch')
            assert np.array_equal(ry, year), (variant,body,'year mismatch')
            data[variant][body] = np.array([float(r['residual_deg']) for r in rs])
            assert np.all(np.isfinite(data[variant][body]))
            alignment.append(f'{variant}/{body}: exact JD and year alignment')
    assert len(np.unique(jd)) == len(jd)
    assert np.all(np.diff(jd) == 10)
    cy, cm, cd = calendar(jd)
    ystart = january_jd(cy, jd >= 2299160.5)
    ynext = january_jd(cy+1, jd >= 2299160.5)
    # The mixed-calendar year 1582 starts Julian and ends Gregorian.
    ystart = np.where(cy == 1582, january_jd(1582, False), ystart)
    ynext = np.where(cy == 1582, january_jd(1583, True), ynext)
    calendary = cy + (jd-ystart)/(ynext-ystart)
    century = 1550 + 100*np.floor((year-1550)/100).astype(int)
    calcentury = 1550 + 100*np.floor((cy-1550)/100).astype(int)
    report['grid'] = {
        'epochs':len(jd), 'rows_per_variant':len(jd)*8,
        'jd_first_last':jd[[0,-1]].tolist(), 'csv_year_first_last':year[[0,-1]].tolist(),
        'calendar_first_last':[(int(cy[i]),int(cm[i]),float(cd[i])) for i in [0,-1]],
        'calendar_fraction_first_last':calendary[[0,-1]].tolist(),
        'year_disagreement_days_range':[(float(np.min((year-calendary)*365.25))),float(np.max((year-calendary)*365.25))],
        'calendar_century_misbinned_epochs':int(np.sum(calcentury != century)),
        'misbinned_rows':[{'jd':float(jd[i]),'csv_year':float(year[i]),'calendar':(int(cy[i]),int(cm[i]),float(cd[i]))} for i in np.where(calcentury!=century)[0]],
        'alignment':alignment,
        'century_counts':{int(c):int(np.sum(century==c)) for c in np.unique(century)},
        'frame_subtraction_roundoff_max':float(np.max(np.abs(aya-prec-frame))),
    }
    computed = {}
    discrepancy = {}
    for variant in data:
        published = {(int(r['century_start_year']),r['body']):r for r in records('century_'+variant+'.csv')}
        computed[variant] = {}
        discrepancy[variant] = {k:0. for k in ['n','mean_deg','rms_deg','max_abs_deg','max_signed_deg']}
        for body in BODIES:
            for c in np.unique(century):
                stats = summarize(data[variant][body][century==c])
                computed[variant][int(c),body] = stats
                p = published[int(c),body]
                for key, field in [('n','n'),('mean','mean_deg'),('rms','rms_deg'),('max_abs','max_abs_deg'),('max_signed','max_signed_deg')]:
                    discrepancy[variant][field] = max(discrepancy[variant][field],abs(stats[key]-float(p[field])))
    report['table_checks']['century_files_max_difference_from_raw'] = discrepancy
    md = (DATA/'paper'/'surya-siddhanta-vs-de440.md').read_text(encoding='utf-8')
    lines = md.splitlines()
    for t, field in [(2,'rms'),(3,'max_abs')]:
        start = next(i for i,l in enumerate(lines) if l.startswith(f'**Table {t}.'))
        end = next(i for i in range(start+1,len(lines)) if lines[i].startswith('**Table '))
        errors = []
        checked = 0
        for i in range(start,end):
            cells = [s.strip() for s in lines[i].split('|')[1:-1]]
            if cells and re.fullmatch(r'\d{4}-\d{4}',cells[0]):
                c = int(cells[0][:4])
                for body,shown in zip(BODIES,cells[1:]):
                    expected = f'{computed["deltat"][c,body][field]:.2f}'
                    checked += 1
                    if expected != shown:
                        errors.append({'line':i+1,'body':body,'shown':shown,'expected':expected})
        report['table_checks'][f'table{t}'] = {'checked_cells':checked,'mismatches':errors}
    fitted = {}
    for body in BODIES:
        x = data['deltat'][body]
        star = x-frame
        slope,offset = np.polyfit(year-2100,star,1)
        remainder = star - (offset+slope*(year-2100))
        fitted[body] = remainder
        report['table4'][body] = {'naive':rms(data['naive'][body]),'deltat':rms(x),
                                'naive_minus_deltat':rms(data['naive'][body])-rms(x),'star':rms(star)}
        report['table5'][body] = {'drift_arcsec_yr':float(slope*3600),'offset_2100':float(offset),
                                'periodic_rms':rms(remainder),'periodic_max_abs':float(np.max(np.abs(remainder))),
                                'periodic_rms_by_century':{int(c):rms(remainder[century==c]) for c in np.unique(century)}}
    for t, source, keys, digits in [(4,'table4',['naive','deltat','naive_minus_deltat','star'],[2,2,2,2]),
                                  (5,'table5',['drift_arcsec_yr','offset_2100','periodic_rms'],[2,3,3])]:
        start = next(i for i,l in enumerate(lines) if l.startswith(f'**Table {t}.'))
        end = next(i for i in range(start+1,len(lines)) if lines[i].startswith('**Table '))
        errors = []
        checked = 0
        for i in range(start,end):
            cells = [s.strip() for s in lines[i].split('|')[1:-1]]
            if cells and cells[0] in BODIES:
                for shown,key,digit in zip(cells[1:],keys,digits):
                    expected = f'{report[source][cells[0]][key]:.{digit}f}'
                    checked += 1
                    if float(expected) != float(shown):
                        errors.append({'line':i+1,'body':cells[0],'field':key,'shown':shown,'expected':expected})
        report['table_checks'][f'table{t}'] = {'checked_cells':checked,'mismatches':errors}
    selected = [0,int(np.argmin(np.abs(year-2100))),int(np.argmax(aya)),int(np.argmin(np.abs(year-2400))),len(jd)-1]
    report['table6'] = [{'jd':float(jd[i]),'year':float(year[i]),'ss':float(aya[i]),'true':float(prec[i]),'difference':float(frame[i])} for i in selected]
    cross = np.where((frame[:-1]>0)&(frame[1:]<0))[0][0]
    crossyear = year[cross] + (year[cross+1]-year[cross]) * frame[cross] / (frame[cross]-frame[cross+1])
    e = data['deltat']['Moon']-data['deltat']['Sun']
    report['discussion']['elongation'] = {**summarize(e),'mae_deg':float(np.mean(np.abs(e))),
        'mean_rate_proxy_hours':float(np.mean(np.abs(e))/12.19*24),
        'max_proxy_hours':float(np.max(np.abs(e))/12.19*24),'epochs_above_12_deg':int(np.sum(np.abs(e)>12))}
    report['discussion']['frame'] = {'zero_cross_year':float(crossyear),
        'post_turn_drift_arcsec_yr':float(np.polyfit(year[year>2300],frame[year>2300],1)[0]*3600),
        'pre_turn_drift_arcsec_yr':float(np.polyfit(year[year<2299],frame[year<2299],1)[0]*3600)}
    report['discussion']['moon_time_mean_change_by_century'] = {int(c):float(np.mean((data['naive']['Moon']-data['deltat']['Moon'])[century==c])) for c in np.unique(century)}
    report['discussion']['venus_fraction_absolute_detrended_over_10'] = float(np.mean(np.abs(fitted['Venus'])>10))
    report['discussion']['rahu_17_sample_moving_average'] = {m:rms(np.convolve(data['deltat']['Rahu'],np.ones(17)/17,mode=m)) for m in ['valid','same','full']}
    for body in ['Jupiter','Saturn']:
        w = 2*np.pi*(year-2100)/883
        design = np.column_stack([np.ones(len(jd)),year-2100,np.sin(w),np.cos(w)])
        beta = np.linalg.lstsq(design,data['deltat'][body]-frame,rcond=None)[0]
        report['discussion'][body+'_883_year_fit'] = {'drift_arcsec_yr':float(beta[1]*3600),
            'amplitude_arcmin':float(np.hypot(beta[2],beta[3])*60),'rms':rms(data['deltat'][body]-frame-design@beta)}
    report['discussion']['means_selected'] = {f'{body}_{c}':computed['deltat'][c,body]['mean'] for body,c in [('Sun',1550),('Sun',2150),('Sun',2550),('Jupiter',2350),('Jupiter',2450),('Rahu',2350),('Rahu',2450)]}
    # Recalculate century RMS using the actual calendar dates to assess the year-label issue.
    report['calendar_century_rms_changes'] = {body:{int(c):rms(data['deltat'][body][calcentury==c])-computed['deltat'][int(c),body]['rms'] for c in np.unique(century)} for body in BODIES}
    output = Path(__file__).with_name('numerics_results.json')
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ['grid','table_checks','table4','table6','discussion']},indent=2))
    print('Wrote',output)

if __name__ == '__main__':
    main()
