return {
  'akinsho/git-conflict.nvim',

  event = { 'BufReadPre', 'BufNewFile' },

  config = function ()
    require('git-conflict').setup()
  end
}
