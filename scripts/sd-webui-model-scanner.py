import os
import torch
import launch
import gradio as gr
import importlib.util

from pathlib import Path
from modules import shared, script_callbacks, ui

import picklescan.scanner as ps
_spec_pi = importlib.util.spec_from_file_location(
    'pickle_inspector',
    os.path.join(
        os.environ.get('SD_PS_DIR', launch.repo_dir('stable-diffusion-pickle-scanner')),
        'pickle_inspector.py'
    )
)
pi = importlib.util.module_from_spec(_spec_pi)
_spec_pi.loader.exec_module(pi)
del _spec_pi

pi.EXTENSIONS = { '.pt', '.bin', '.ckpt' }
pi.BAD_CALLS = { 'os', 'shutil', 'sys', 'requests', 'net' }
pi.BAD_SIGNAL = { 'rm ', 'cat ', 'nc ', '/bin/sh ' }
pi.NON_STANDARD = { 'numpy.', '_codecs.', 'collections.', 'torch.' }

ps.EXTENSIONS = {
    '.npy', '.bin', '.pt', '.pth', '.ckpt',
    '.pkl', '.pickle', '.joblib', '.dat', '.data',
    '.zip', '.npz',
}

TEMPLATE = '''
<h2>Results:</h2>
<table class="sd-webui-model-scanner-results">
    <thead>
        <tr><th>Target</th><th>Notes</th><th>Warnings</th><th>Alerts</th><th>Errors</th></tr>
    </thead>
    <tbody>{rows}</tbody>
</table>
'''

def show_results(results):
    rows = []
    for target, scanres in results.items():
        row = ''
        details = ''
        alerts, warns, errs, notes = [], [], [], []
        
        if 'errors' in scanres:
            scandata = scanres['errors']
            errs.extend(scandata)
            details += '<h3>Errors</h3><table class="sd-webui-model-scanner-results-errors"><tbody>'
            for error in scandata: details += f'<tr><td>{error}</td></tr>'
            details += '</tbody></table>'

        if 'picklescan' in scanres:
            scandata = scanres['picklescan']
            ps.ScanResult
            details += '<h3>PickleScan</h3><table class="sd-webui-model-scanner-results-picklescan">'
            details += '<thead><tr><th>Module</th><th>Name</th><th>Severity</th></tr></thead><tbody>'
            for g in scandata.globals:
                safstr = str(g.safety).replace('SafetyLevel.', '').lower()
                if g.safety == ps.SafetyLevel.Dangerous: alerts.append(f'{g.module} - {g.name}')
                elif g.safety == ps.SafetyLevel.Suspicious: warns.append(f'{g.module} - {g.name}')
                details += f'<tr class="sd-webui-model-scanner-results-picklescan-{safstr}"><td>{g.module}</td><td>{g.name}</td><td>{safstr}</td></tr>'
            details += '</tbody></table>'

        if 'sd-scanner' in scanres:
            scandata = scanres['sd-scanner']
            details += '<h3>SD Pickle Scanner</h3><table class="sd-webui-model-scanner-results-sdscanner">'
            details += '<thead><tr><th>Name</th><th>Class</th></tr></thead><tbody>'
            for i in scandata['bad_calls']: details += f'<tr class="sd-webui-model-scanner-results-sdscanner-badcall"><td>{i}</td><td>Bad Call</td></tr>'
            for i in scandata['bad_signals']: details += f'<tr class="sd-webui-model-scanner-results-sdscanner-badsignal"><td>{i}</td><td>Bad Signal</td></tr>'
            for i in scandata['non_standard']: details += f'<tr class="sd-webui-model-scanner-results-sdscanner-nonstd"><td>{i}</td><td>Non-Standard</td></tr>'
            details += '</tbody></table>'
            alerts.extend(list(scandata['bad_calls']) + list(scandata['bad_signals']))
            notes.extend(list(scandata['non_standard']))

        n_alerts, n_warnings, n_errors, n_notes = len(alerts), len(warns), len(errs), len(notes)
        row += f'<td>{target}</td><td>{n_notes}</td><td>{n_warnings}</td><td>{n_alerts}</td><td>{n_errors}</td>'
        style_cls = [ 'sd-webui-model-scanner-results-r1' ]
        if n_errors: style_cls.append('sd-webui-model-scanner-results-error')
        if n_alerts: style_cls.append('sd-webui-model-scanner-results-alert')
        if n_warnings: style_cls.append('sd-webui-model-scanner-results-warning')
        if n_notes: style_cls.append('sd-webui-model-scanner-results-note')
        row = f'<tr class="{str.join(" ", style_cls)}">{row}</tr>'

        style_cls[0] = 'sd-webui-model-scanner-results-r2'
        row += f'<tr class="{str.join(" ", style_cls)}"><td colspan="5"><details><summary>Scanner Details</summary>{details}</details></td></tr>'
        rows.append(row)
    return TEMPLATE.format(rows=str.join('', rows))

def scan_sd_model(path):
    result = torch.load(
        path.as_posix(),
        pickle_module=pi.pickle
    )
    results = dict(bad_calls=set(), bad_signals=set(), non_standard=set())
    for c in result.calls:
        for call in pi.BAD_CALLS:
            if c.find(call + '.') == 0:
                results['bad_calls'].add(call)
        for signal in pi.BAD_SIGNAL:
            if c.find(signal) > -1:
                results['bad_signals'].add(signal.strip())
        for ns in pi.NON_STANDARD:
            if c.find(ns) != 0:
                results['non_standard'].add(ns.rstrip('.'))
    return results

def scan_model(targets):
    if not targets: targets = shared.models_path
    if type(targets) is str: targets = [ v.strip() for v in targets.split(';') ]
    results = dict()
    
    for target in targets:
        try:
            target_path = Path(target).absolute()

            if target.startswith('https://huggingface.co/'):
                results[target] = dict()
                results[target]['picklescan'] = ps.scan_url(target)

            elif target_path.is_dir():
                for sub_path in target_path.glob(r'**/*'):
                    raw_sub_path = str(sub_path.absolute())
                    if sub_path.suffix in ps.EXTENSIONS:
                        results[raw_sub_path] = results.get(raw_sub_path, dict())
                        results[raw_sub_path]['picklescan'] = ps.scan_file_path(sub_path)
                    if sub_path.suffix in pi.EXTENSIONS:
                        results[raw_sub_path] = results.get(raw_sub_path, dict())
                        results[raw_sub_path]['sd-scanner'] = scan_sd_model(sub_path)

            elif target_path.is_file():
                raw_target_path = str(target_path)
                results[raw_target_path] = results.get(raw_target_path, dict())
                results[raw_target_path]['picklescan'] = ps.scan_file_path(str(target_path))
                results[raw_target_path]['sd-scanner'] = scan_sd_model(target_path)

            else:
                results[target] = results.get(target, dict())
                try: results[target]['picklescan'] = ps.scan_huggingface_model(target)
                except RuntimeError as ex:
                    if not len(ex.args) or type(ex.args[0]) is not str or not ex.args[0].startswith('HTTP '): raise ex
                    results[target]['errors'] = [ f'Target path does not exists or is not a valid HuggingFace Model ID: "{target_path}"' ]
        except Exception as gex:
            print('EX:', gex)
            results[target]['errors'] = [ str(gex) ]
    return show_results(results)

def add_tab():
    with gr.Blocks(analytics_enabled=False) as tab:
        with gr.Row():
            with gr.Column():
                gr.Markdown('''## Inputs

Targets can be:
- a directory
- a model file
- a Hugging Face Hub Model ID ***(downloaded from internet, NOT CACHED)***
- a link to a Hugging Face Hub repository ***(downloaded from internet, NOT CACHED)***
If left empty, the security scanners will check the default model directory.\\
You can separate multiple targets with a `;`.
''')
                model_scanner = gr.Textbox(label='Targets', placeholder='(Optional)')
                scan = gr.Button('Scan', variant='primary')
                # stop = gr.Button('Interrupt') # TODO: add a working interruption button

                results = gr.HTML(TEMPLATE.format(rows='') + '<hr/><h3>Run a scan to see the results</h3>')

        scan_evt = scan.click(
            fn=scan_model,
            inputs=[model_scanner],
            outputs=[results]
        )
        # NOTE: "cancels" does not stop the downloading operation!
        # stop.click(fn=None, cancels=[ scan_evt ])

    return [ (tab, 'Model Scanner', "model-scanner") ]

script_callbacks.on_ui_tabs(add_tab)

VERSION = '0.1.0'