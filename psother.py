def true_args(arg_list, any=False, **kwargs):
    """Check if all arguments are in kwargs. 
       If any is set to True, then return True if any of the args in the list
       is set to True in kwargs. 
    """
    is_true = None
    for arg in arg_list:
        if arg in kwargs:
            if not kwargs[arg]:
                is_true = False
            elif any or is_true is None:
                is_true = True
        else:
            if not any:
                is_true = False
    return is_true

def args_list_flatten(*args):
    try:
        return [item for sublist in args for item in sublist]
    except:
        print 'Cannot flatten list of args: ', args


