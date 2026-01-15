#!/bin/bash
# Bash completion script for SMRForge CLI
# Install: source this file or copy to /etc/bash_completion.d/smrforge

_smrforge_completion() {
    local cur prev opts base
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main commands
    base_commands="serve shell config reactor data burnup validate visualize workflow"
    
    # Subcommands
    reactor_commands="create analyze list compare"
    data_commands="setup download validate"
    burnup_commands="run visualize"
    validate_commands="run"
    visualize_commands="geometry flux burnup"
    config_commands="show set init"
    workflow_commands="run"
    
    case "${COMP_CWORD}" in
        1)
            COMPREPLY=($(compgen -W "${base_commands}" -- ${cur}))
            return 0
            ;;
        2)
            case "${prev}" in
                reactor)
                    COMPREPLY=($(compgen -W "${reactor_commands}" -- ${cur}))
                    return 0
                    ;;
                data)
                    COMPREPLY=($(compgen -W "${data_commands}" -- ${cur}))
                    return 0
                    ;;
                burnup)
                    COMPREPLY=($(compgen -W "${burnup_commands}" -- ${cur}))
                    return 0
                    ;;
                validate)
                    COMPREPLY=($(compgen -W "${validate_commands}" -- ${cur}))
                    return 0
                    ;;
                visualize)
                    COMPREPLY=($(compgen -W "${visualize_commands}" -- ${cur}))
                    return 0
                    ;;
                config)
                    COMPREPLY=($(compgen -W "${config_commands}" -- ${cur}))
                    return 0
                    ;;
                workflow)
                    COMPREPLY=($(compgen -W "${workflow_commands}" -- ${cur}))
                    return 0
                    ;;
            esac
            ;;
    esac
    
    # Handle options
    case "${prev}" in
        --reactor|--config|--output|--workflow)
            COMPREPLY=($(compgen -f -- ${cur}))
            return 0
            ;;
        --preset)
            # Could query presets, but for now just complete common ones
            COMPREPLY=($(compgen -W "valar-10 valar-50" -- ${cur}))
            return 0
            ;;
        --format)
            COMPREPLY=($(compgen -W "json yaml" -- ${cur}))
            return 0
            ;;
        --library)
            COMPREPLY=($(compgen -W "ENDF-B-VIII.1 ENDF-B-VIII.0" -- ${cur}))
            return 0
            ;;
        --type)
            COMPREPLY=($(compgen -W "htgr pwr bwr fast" -- ${cur}))
            return 0
            ;;
    esac
    
    return 0
}

complete -F _smrforge_completion smrforge
