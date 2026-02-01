# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/Users/Alex/miniforge3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/Users/Alex/miniforge3/etc/profile.d/conda.sh" ]; then
        . "/Users/Alex/miniforge3/etc/profile.d/conda.sh"
    else
        export PATH="/Users/Alex/miniforge3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

# Optional pyenv setup (keep only if you really want pyenv later)
# export PATH="$HOME/.pyenv/bin:$PATH"
# eval "$(pyenv init --path)"
# eval "$(pyenv init -)"
# eval "$(pyenv virtualenv-init -)"

# Local binaries (put AFTER conda so conda Python takes priority)
export PATH=/opt/local/bin:/opt/local/sbin:$PATH

# >>> mamba initialize >>>
# !! Contents within this block are managed by 'mamba shell init' !!
export MAMBA_EXE='/Users/Alex/miniforge3/bin/mamba';
export MAMBA_ROOT_PREFIX='/Users/Alex/miniforge3';
__mamba_setup="$("$MAMBA_EXE" shell hook --shell zsh --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias mamba="$MAMBA_EXE"  # Fallback on help from mamba activate
fi
unset __mamba_setup
# <<< mamba initialize <<<
export TELEGRAM_BOT_TOKEN=8590413563:AAHMAeDnbSFwd9UCu_lW_vv_rcyILDZiIJ8
