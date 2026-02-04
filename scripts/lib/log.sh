# Log helpers: colors only when stdout is a TTY (pipes/CI stay plain).
if [[ -t 1 ]]; then
  _c_red='\033[0;31m'
  _c_green='\033[0;32m'
  _c_yellow='\033[0;33m'
  _c_cyan='\033[0;36m'
  _c_dim='\033[2m'
  _c_bold='\033[1m'
  _c_reset='\033[0m'
else
  _c_red= _c_green= _c_yellow= _c_cyan= _c_dim= _c_bold= _c_reset=
fi

log_section() { echo ""; echo -e "${_c_bold}${_c_cyan}$*${_c_reset}"; }
log_line()    { echo -e "${_c_dim}────────────────────────────────────────${_c_reset}"; }
log_step()    { echo -e "${_c_cyan}==>${_c_reset} $*"; }
log_info()    { echo -e "${_c_dim}  $*${_c_reset}"; }
log_ok()      { echo -e "  ${_c_green}✓${_c_reset} $*"; }
log_warn()    { echo -e "  ${_c_yellow}⚠${_c_reset} $*"; }
log_fail()    { echo -e "  ${_c_red}✗${_c_reset} $*" >&2; }
log_err()     { echo -e "${_c_red}$*${_c_reset}" >&2; }
