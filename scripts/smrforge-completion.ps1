# PowerShell completion script for SMRForge CLI
# Install: Add to PowerShell profile: . .\scripts\smrforge-completion.ps1

Register-ArgumentCompleter -Native -CommandName smrforge -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $commands = @(
        'serve', 'shell', 'config', 'reactor', 'data', 
        'burnup', 'validate', 'visualize', 'workflow'
    )
    
    $reactorCommands = @('create', 'analyze', 'list', 'compare')
    $dataCommands = @('setup', 'download', 'validate')
    $burnupCommands = @('run', 'visualize')
    $validateCommands = @('run')
    $visualizeCommands = @('geometry', 'flux', 'burnup')
    $configCommands = @('show', 'set', 'init')
    $workflowCommands = @('run')
    
    $commandParts = $commandAst.CommandElements | ForEach-Object { $_.ToString() }
    $wordCount = $commandParts.Count
    
    if ($wordCount -eq 2) {
        $commands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
    }
    elseif ($wordCount -eq 3) {
        $mainCommand = $commandParts[1]
        switch ($mainCommand) {
            'reactor' { 
                $reactorCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            'data' { 
                $dataCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            'burnup' { 
                $burnupCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            'validate' { 
                $validateCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            'visualize' { 
                $visualizeCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            'config' { 
                $configCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            'workflow' { 
                $workflowCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
        }
    }
}
