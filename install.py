import os
import launch

if not launch.is_installed('picklescan'):
    launch.run_pip(
        command='install picklescan',
        desc='requirements for ModelScanner'
    )

SD_PS_DIR = os.environ.get(
    'SD_PS_DIR',
    launch.repo_dir('stable-diffusion-pickle-scanner')
)
if not os.path.exists(SD_PS_DIR):
    launch.git_clone(
        url='https://github.com/zxix/stable-diffusion-pickle-scanner',
        name='stable-diffusion-pickle-scanner',
        dir=SD_PS_DIR
    )