import guild.runs_cmd

def main(args, ctx):
    runs = guild.runs_cmd.runs_for_args(args, ctx)
    print("TODO: launch TensorBoard to view %s" % runs)
