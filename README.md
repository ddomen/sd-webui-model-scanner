# sd-webui-model-scanner
Enable running security checks directly from the webui interface.

# Disclaimer
The author is not responsibile for any action taken after the use of this piece of software, or either any damage caused by the use of it. This software just employes some tools to make an utility chain in order to facilitate the sanity checking of the donwloaded models.\
**IMPORTANT: This extension WILL NOT PREVENT in any way the use of dangerous or suspicious models, it will just warn the user that something unusual can be performed while loading those models.**\
The employed sanity checkers could also possibly detect false positives.

# Installation

Follow these steps:
1. Launch the WebUI interface.
2. Select the `Extensions` tab and go to `Install from URL` (or `Manual Install`)
3. Paste the link to this repository: `https://github.com/ddomen/sd-webui-model-scanner`
4. Click `Install`
5. Click `Apply and restart the UI` (button under `Extensions > Installed`) or manually restart the WebUI

Than the extension will automatically install the needed packages

# Usage

When the extension is activated, go in the tab `Model Scanner` and follow the instructions. You can fill the `Targets` input and scan:
- a directory
- a model file
- a Hugging Face Hub Model ID *(downloaded from internet, **NOT CACHED/PERSISTED**)*
- a link to a Hugging Face Hub repository *(downloaded from internet, **NOT CACHED/PERSISTED**)*

If the `Targets` is left empty, the security scanners will check the default model directory.

**WARN:** once the download of a model started, the only actual way to stop it is to wait it completes or shutting down the WebUI process (`SIGKILL` or `CTRL-C` for Windows users). Be sure to start a download only if you can complete it or you can interrupt the WebUI process.

**NOTE:** only the actual model files are checked, metadata files attached to the model, with an extension not included in the supported formats, are ignored

# Sanity Checkers
These are the actual sanity checkers employed in the process (and required by this extension):
|Name|GitHub|Supported Extensions|
|:--:|:----:|:-------------------|
|Stable Diffusion Pickle Scanner|https://github.com/zxix/stable-diffusion-pickle-scanner|`pt`, `bin`, `ckpt`|
|Pickle Scan|https://github.com/mmaitre314/picklescan|`npy`, `bin`, `pt`, `pth`, `ckpt`, `pkl`, `pickle`, `joblib`, `dat`, `data`, `zip`, `npz`|

# Results
The results will be displayed in a table:
|Severity|Color|Details|
|:------:|:---:|:------|
|**Innocuos**|Black / White (theme color)|Nothing to report|
|**Note**|Yellow|The model uses some unconventional but usually innocuous libraries (such as `numpy`)|
|**Warning**|Orange|The model presents some potential risk or suspicious import which could harm the computer or the user data (it could perform some disk operations bound to model loading - eg. uses `pytorch_lightning.callbacks.model_checkpoint.ModelCheckpoint`)|
|**Alert**|Red|The model employes libraries or techniques reputed to be malevoulous (such as requiring modules to perform internet `requests` or calling shell commands like `rm`) and will most probably harm the machine or the user data if loaded. **Handle it with much care** (or just throw it away)!|
|**Error**|Purple|Some error was raised while performing the sanity check. This is usually a symptom of a bad work of this extension. Note that this extension can usually check all of the most common kind of models, so handle a model which raised an error with care |

You can see further explanation of the sanity check by expanding the row `Scanner Details` in order to explore the reasons the system rejected the sanity of a model. In this subsection you will presented with a table for each sanity checker showing their results.

# FAQs
## Why no `safetensor` extension support?
`safetensor` model, as the extension says, are mostly safe by their own. This extension has a different standard and will not use `pickle/unpickle`, which is usually the main source of threats in model loading.\
Citing [Hugging Face safetensor Security Audit](https://huggingface.co/blog/safetensors-security-audit#the-security-audit):
> While it is impossible to prove the absence of flaws, this is a major step in giving reassurance that `safetensors` is indeed safe to use.

# Issues & todo
- [ ] Improve results styling
- [ ] Cache downloaded models
- [ ] Allow to insert any url to download a model
- [ ] Make an interrupt button to stop long running checks *(useful for models checked from net connections)*
