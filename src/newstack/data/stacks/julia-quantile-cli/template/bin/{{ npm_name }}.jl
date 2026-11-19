#!/usr/bin/env julia

using Quantiles

const PROGRAM = "{{ npm_name }}"

function main(argv)
    return Quantiles.run(argv)
end

exit(main(ARGS))
