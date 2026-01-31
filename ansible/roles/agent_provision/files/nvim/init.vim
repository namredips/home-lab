
" ******  VIM PLUG ******
" The default plugin directory will be as follows:
"   - Vim (Linux/macOS): '~/.vim/plugged'
"   - Vim (Windows): '~/vimfiles/plugged'
"   - Neovim (Linux/macOS/Windows): stdpath('data') . '/plugged'
" You can specify a custom plugin directory by passing it as the argument
"   - e.g. `call plug#begin('~/.vim/plugged')`
"   - Avoid using standard Vim directory names like 'plugin'
" docs at: https://github.com/junegunn/vim-plug
"
" Initialize plugin system
call plug#begin()
Plug 'bling/vim-bufferline'
Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
Plug 'ivanov/vim-ipython'
Plug 'tmhedberg/SimpylFold'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'tpope/vim-fugitive'
Plug 'APZelos/blamer.nvim'
Plug 'github/copilot.vim'
Plug 'Raimondi/delimitMate'
Plug 'tpope/vim-surround'
"Plug 'flazz/vim-colorschemes'
Plug 'mrk21/yaml-vim'
Plug 'pedrohdz/vim-yaml-folds'
Plug 'sheerun/vim-polyglot'
Plug 'heavenshell/vim-pydocstring', { 'do': 'make install', 'for': 'python' }
Plug 'dart-lang/dart-vim-plugin'
Plug 'thosakwe/vim-flutter'
Plug 'dense-analysis/ale'
Plug 'iamcco/markdown-preview.nvim', { 'do': { -> mkdp#util#install() }, 'for': ['markdown', 'vim-plug']}
Plug 'nvim-lua/plenary.nvim'
Plug 'nvim-treesitter/nvim-treesitter', {'branch': 'master'}
Plug 'nvim-treesitter/playground'
Plug 'olimorris/codecompanion.nvim'
Plug 'MeanderingProgrammer/render-markdown.nvim', 
Plug 'nvim-telescope/telescope.nvim'
Plug 'echasnovski/mini.nvim'
Plug 'nvim-tree/nvim-web-devicons'
Plug 'navarasu/onedark.nvim'
Plug 'nvim-tree/nvim-web-devicons'
Plug 'nvim-tree/nvim-tree.lua'
Plug 'tpope/vim-commentary'
Plug 'williamboman/mason.nvim'
Plug 'williamboman/mason-lspconfig.nvim'
Plug 'neovim/nvim-lspconfig'
Plug 'hrsh7th/cmp-nvim-lsp'
Plug 'hrsh7th/cmp-buffer'
Plug 'hrsh7th/cmp-path'
Plug 'hrsh7th/cmp-cmdline'
Plug 'hrsh7th/nvim-cmp'

call plug#end()

" require lua files that have lua based configs
"
lua require('onedark_settings')
lua require('codecompanion_settings')
lua require('render_markdown')
lua require('treesitter')
lua require('telescope_settings')
lua require('nvim_tree')
lua require('mason_settings')
lua require('mason_lspconfig_settings')
lua require('nvim_cmp_settings')

" **** Global settings ****
set bg=light
highlight clear SignColumn


let g:coc_global_extensions = [ 'coc-pyright', 'coc-flutter-tools' ]
set encoding=utf-8
set nocompatible
syntax enable
set nohlsearch
"filetype off
set tabstop=2
set shiftwidth=2
set expandtab
set splitright
set splitbelow
set noshowmode
set t_Co=256
highlight clear SignColumn

"
" *** COC general configurations ***
"
" *** coc floating window colors  ***
"
"highlight CocFloating ctermbg=60 ctermfg=7 guibg=#3a3a3a guifg=#dcdccc
"highlight Pmenu ctermbg=60 ctermfg=7 guibg=#3a3a3a guifg=#dcdccc

" *** coc diagnostics colors  ***
"

if has('nvim-0.4.3') || has('patch-8.2.0750')
	nnoremap <nowait><expr> <C-f> coc#float#has_scroll() ? coc#float#scroll(1) : "\<C-f>"
  nnoremap <nowait><expr> <C-b> coc#float#has_scroll() ? coc#float#scroll(0) : "\<C-b>"
  inoremap <nowait><expr> <C-f> coc#float#has_scroll() ? "\<c-r>=coc#float#scroll(1)\<cr>" : "\<Right>"
  inoremap <nowait><expr> <C-b> coc#float#has_scroll() ? "\<c-r>=coc#float#scroll(0)\<cr>" : "\<Left>"
endif


" Applying codeAction to the selected region.
" Example: `<leader>aap` for current paragraph
xmap <leader>a  <Plug>(coc-codeaction-selected)
nmap <leader>a  <Plug>(coc-codeaction-selected)

" Remap keys for applying codeAction to the current buffer.
nmap <leader>ac  <Plug>(coc-codeaction)

" Apply AutoFix to problem on the current line.
nmap <leader>qf  <Plug>(coc-fix-current)

" Run the Code Lens action on the current line.
nmap <leader>cl  <Plug>(coc-codelens-action)

" *** end COC general

"
" vim-airline configurations
"
let g:airline_powerline_fonts = 1

if !exists('g:airline_symbols')
    let g:airline_symbols = {}
endif

" for tmuxline + vim-airline integration
let g:airline#extensions#tmuxline#enabled = 1

" for coc + vim-airline integration
let g:airline#extensions#coc#enabled = 1

" unicode symbols
"let g:airline_left_sep = '»'
let g:airline_left_sep = "\ue0b0"
"let g:airline_right_sep = '«'
"let g:airline_right_sep = '◀'
let g:airline_right_sep = "\ue0b2"
let g:airline_symbols.linenr = '␊'
"let g:airline_symbols.linenr = '␤'
"let g:airline_symbols.linenr = '¶'
let g:airline_symbols.branch = '⎇'
let g:airline_symbols.branch = "\ue0a0"
let g:airline_symbols.paste = 'ρ'
let g:airline_symbols.paste = 'Þ'
let g:airline_symbols.paste = '∥'
let g:airline_symbols.whitespace = 'Ξ'

set laststatus=2

" vim-airline configuration end


"
" ale
"
let g:ale_virtualtext_cursor=0
let g:airline#extensions#ale#enabled = 1
let g:ale_disable_lsp = 1
let g:ale_lint_on_save = 1
let g:ale_lint_on_text_changed = 'never'
let g:ale_lint_on_insert_leave = 0
let g:ale_list_window_size = 5
let g:ale_open_list = 1
let g:ale_fix_on_save = 1
let g:ale_lint_on_enter = 0
let g:ale_sign_error  = "\uF704\uF704"
"let g:ale_sign_warning = "\uF071"
let g:ale_sign_style_error = 'CC'
let g:ale_sign_warning = '≈≈'
let b:ale_linters = {'python': ['ruff'], 'dart': ['dart_analyze'], 'json': ['jsonlint']}
let b:ale_fixers = {'python': ['isort', 'ruff_format', 'fixjson'], 'json': ['fixjson', 'prettier'], 'dart': ['dart-format'] }
let g:ale_python_ruff_use_global = 1


"highlight ALEError ctermfg=LightRed ctermbg=Red
highlight ALEErrorSign ctermfg=Red ctermbg=black guifg=Red guibg=black
"highlight ALEStyleError ctermfg=LightBlue ctermbg=Blue
highlight ALEStyleErrorSign ctermfg=Blue ctermbg=Black guifg=Blue guibg=Black
"highlight ALEWarning ctermbg=Yellow
highlight ALEWarningSign ctermfg=Yellow ctermbg=black guifg=Yellow guibg=black
"highlight ALEStyleWarning ctermfg=Yellow ctermbg=black
"highlight ALEInfo ctermfg=LightBlue ctermbg=Blue
"highlight ALEInfoLine ctermfg=LightBlue ctermbg=Blue
"hi SpellBad ctermfg=Blue cterm=underline
hi Search ctermbg=None ctermfg=green guibg=None guifg=green
augroup CloseLoclistWindowGroup
  autocmd!
  autocmd QuitPre * if empty(&buftype) | lclose | endif
augroup END

" *** coc-git ***
"
" Clear background from git symbols
highlight clear DiffAdd
highlight clear DiffChange
highlight clear DiffDelete
highlight DiffDelete ctermfg=blue guifg=blue
highlight DiffAdd ctermfg=green guifg=green
highlight DiffChange ctermfg=yellow guifg=yellow
let g:gitgutter_override_sign_column_highlight=0

" SimplyFold
let g:SimpylFold_docstring_preview=1

" *** LANGUAGES ***
"
"python
"
autocmd FileType python call SetPythonOptions()
function SetPythonOptions()
  setlocal cc=88
  setl et ts=4 sw=4 number
  set background=light
  highlight clear SignColumn
endfunction

"
"Dart/Flutter
"
"let g:lsc_auto_map = v:true
let g:dart_style_guide = 2
let g:dart_format_on_save = 1
autocmd BufEnter *.dart call SetDartOptions()
function SetDartOptions()
  setl number
  set background=dark
  highlight clear SignColumn
endfunction

au! BufNewFile,BufReadPost *.{dart} set filetype=dart foldmethod=syntax

"yaml
augroup yaml_settings
  autocmd!
  autocmd BufNewFile,BufReadPost *.{yaml,yml,yaml.j2,yml.j2} set filetype=yaml
  autocmd FileType yaml setlocal ts=2 sts=2 sw=2 expandtab indentkeys-=0#
augroup END
"au! BufNewFile,BufReadPost *.{yaml,yml,yaml.j2,yml.j2} set filetype=yaml
"autocmd FileType yaml setlocal ts=2 sts=2 sw=2 expandtab indentkeys-=0#

"json
au! BufNewFile,BufReadPost *.{json} set filetype=json foldmethod=syntax

" *** END LANGUAGES

" MARKDOWN CONFIG
" set to 1, nvim will open the preview window after entering the markdown buffer
" default: 0
let g:mkdp_auto_start = 0

" set to 1, the nvim will auto close current preview window when change
" from markdown buffer to another buffer
" default: 1
let g:mkdp_auto_close = 1

" set to 1, the vim will refresh markdown when save the buffer or
" leave from insert mode, default 0 is auto refresh markdown as you edit or
" move the cursor
" default: 0
let g:mkdp_refresh_slow = 0

" set to 1, the MarkdownPreview command can be use for all files,
" by default it can be use in markdown file
" default: 0
let g:mkdp_command_for_global = 1

" set to 1, preview server available to others in your network
" by default, the server listens on localhost (127.0.0.1)
" default: 0
let g:mkdp_open_to_the_world = 0

" use custom IP to open preview page
" useful when you work in remote vim and preview on local browser
" more detail see: https://github.com/iamcco/markdown-preview.nvim/pull/9
" default empty
let g:mkdp_open_ip = ''

" specify browser to open preview page
" for path with space
" valid: `/path/with\ space/xxx`
" invalid: `/path/with\\ space/xxx`
" default: ''
let g:mkdp_browser = ''

" set to 1, echo preview page url in command line when open preview page
" default is 0
let g:mkdp_echo_preview_url = 0

" a custom vim function name to open preview page
" this function will receive url as param
" default is empty
let g:mkdp_browserfunc = ''

" options for markdown render
" mkit: markdown-it options for render
" katex: katex options for math
" uml: markdown-it-plantuml options
" maid: mermaid options
" disable_sync_scroll: if disable sync scroll, default 0
" sync_scroll_type: 'middle', 'top' or 'relative', default value is 'middle'
"   middle: mean the cursor position alway show at the middle of the preview page
"   top: mean the vim top viewport alway show at the top of the preview page
"   relative: mean the cursor position alway show at the relative positon of the preview page
" hide_yaml_meta: if hide yaml metadata, default is 1
" sequence_diagrams: js-sequence-diagrams options
" content_editable: if enable content editable for preview page, default: v:false
" disable_filename: if disable filename header for preview page, default: 0
let g:mkdp_preview_options = {
    \ 'mkit': {},
    \ 'katex': {},
    \ 'uml': {},
    \ 'maid': {},
    \ 'disable_sync_scroll': 0,
    \ 'sync_scroll_type': 'middle',
    \ 'hide_yaml_meta': 1,
    \ 'sequence_diagrams': {},
    \ 'flowchart_diagrams': {},
    \ 'content_editable': v:false,
    \ 'disable_filename': 0,
    \ 'toc': {}
    \ }

" use a custom markdown style must be absolute path
" like '/Users/username/markdown.css' or expand('~/markdown.css')
" let g:mkdp_markdown_css = ''

" use a custom highlight style must absolute path
" like '/Users/username/highlight.css' or expand('~/highlight.css')
" let g:mkdp_highlight_css = ''

" use a custom port to start server or empty for random
let g:mkdp_port = ''

" preview page title
" ${name} will be replace with the file name
let g:mkdp_page_title = '「${name}」'

" recognized filetypes
" these filetypes will have MarkdownPreview... commands
let g:mkdp_filetypes = ['markdown','md']

" set default theme (dark or light)
" By default the theme is define according to the preferences of the system
" let g:mkdp_theme = 'dark'

augroup JumpCursorOnEdit
     au!
      autocmd BufReadPost *
       \ if expand("<afile>:p:h") !=? $TEMP |
       \ if line("'\"") > 1 && line("'\"") <= line("$") |
       \ let JumpCursorOnEdit_foo = line("'\"") |
       \ let b:doopenfold = 1 |
       \ if (foldlevel(JumpCursorOnEdit_foo) > foldlevel(JumpCursorOnEdit_foo - 1)) |
       \ let JumpCursorOnEdit_foo = JumpCursorOnEdit_foo - 1 |
       \ let b:doopenfold = 2 |
       \ endif |
       \ exe JumpCursorOnEdit_foo |
       \ endif |
       \ endif
       " Need to postpone using "zv" until after reading the modelines.
         autocmd BufWinEnter *
       \ if exists("b:doopenfold") |
       \ exe "normal zv" |
       \ if(b:doopenfold > 1) |
       \ exe "+".1 |
       \ endif |
       \ unlet b:doopenfold |
       \ endif
augroup END


" Git Blammer
let g:blamer_enabled = 1


" Use tab for trigger completion with characters ahead and navigate.
" NOTE: There's always complete item selected by default, you may want to enable
" no select by `"suggest.noselect": true` in your configuration file.
" NOTE: Use command ':verbose imap <tab>' to make sure tab is not mapped by
" other plugin before putting this into your config.
inoremap <silent><expr> <TAB>
      \ coc#pum#visible() ? coc#pum#next(1) :
      \ CheckBackspace() ? "\<Tab>" :
      \ coc#refresh()
inoremap <expr> <S-TAB> coc#pum#visible() ? coc#pum#prev(1) : "\<S-Tab>"

" Make <CR> to accept selected completion item or notify coc.nvim to format
" <C-g>u breaks current undo, please make your own choice.
inoremap <silent><expr> <CR> coc#pum#visible() ? coc#pum#confirm()
                              \: "\<C-g>u\<CR>\<c-r>=coc#on_enter()\<CR>"

function! CheckBackspace() abort
  let col = col('.') - 1
  return !col || getline('.')[col - 1]  =~# '\s'
endfunction

let g:copilot_filetypes = {
    \ 'gitcommit': v:true,
    \ 'markdown': v:true,
    \ 'yaml': v:true,
    \ 'perl': v:true
    \ }

set mouse=

