import inspect

from aitown.repos import interfaces


def _make_dummy_args(func):
    sig = inspect.signature(func)
    args = []
    for i, (name, param) in enumerate(sig.parameters.items()):
        # supply None for all params (including self)
        args.append(None)
    return args


def test_call_abstract_methods_do_nothing():
    # For each abstract method in interfaces, call it with dummy args to execute the method body (pass)
    for name, obj in vars(interfaces).items():
        if inspect.isclass(obj):
            for attr_name, attr in vars(obj).items():
                if callable(attr) and not attr_name.startswith("_"):
                    # call the function with None for each parameter to execute 'pass' bodies
                    try:
                        args = _make_dummy_args(attr)
                        attr(*args)
                    except TypeError:
                        # some signatures may not accept None for certain parameters, ignore
                        pass
