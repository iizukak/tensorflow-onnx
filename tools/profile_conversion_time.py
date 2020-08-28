# coding: utf-8
"""
Profiles the conversion of a Keras model.
"""
import cProfile, pstats, io
from pstats import SortKey
import fire
import tensorflow as tf
from tf2onnx import tfonnx
from tensorflow.keras.applications import MobileNet, EfficientNetB2
try:
    from pyinstrument import Profiler
except ImportError:
    Profiler = None


def spy_model(name):
    "Creates the model."
    with tf.compat.v1.Session(graph=tf.Graph()) as session:
        if name == "MobileNet":
            model = MobileNet()
        elif name == "EfficientNetB2":
            model = EfficientNetB2()
        else:
            raise ValueError("Unknown model name %r." % name)

        graph_def = tf.compat.v1.graph_util.convert_variables_to_constants(
            sess=session,
            input_graph_def=session.graph_def,
            output_node_names=[model.output.op.name])

    return graph_def, model


def spy_convert(graph_def, model):
    "Converts the model."
    with tf.Graph().as_default() as graph:
        tf.import_graph_def(graph_def=graph_def, name='')

        def spy_convert_in():
            return tfonnx.process_tf_graph(
                tf_graph=graph, input_names=[model.input.name],
                output_names=[model.output.name])

        spy_convert_in()


def create(name):
    "Creates the model."
    graph_def, model = spy_model(name)
    return graph_def, model


def convert(graph_def, model):
    "Converts the model."
    spy_convert(graph_def, model)


def profile(profiler="none", name="MobileNet", show_all=False):
    """
    Profiles the conversion of a model.

    :param profiler: one among none, spy, pyinstrument, cProfile
    :param name: model to profile, MobileNet, EfficientNetB2
    :param show_all: use by pyinstrument to show all functions
    """
    print("create(%r, %r)" % (profiler, name))
    graph_def, model = create(name)
    print("profile(%r, %r)" % (profiler, name))
    if profiler == 'none':
        convert(graph_def, model)
    elif profiler == "spy":
        # py-spy record -r 10 -o profile.svg -- python conversion_time.py spy
        convert(graph_def, model)
    elif profiler == "pyinstrument":
        if Profiler is None:
            raise ImportError("pyinstrument is not installed")
        profiler = Profiler(interval=0.0001)
        profiler.start()
        convert(graph_def, model)
        profiler.stop()
        print(profiler.output_text(unicode=False, color=False, show_all=show_all))
    elif profiler == "cProfile":
        pr = cProfile.Profile()
        pr.enable()
        convert(graph_def, model)
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
    else:
        raise ValueError("Unknown profiler %r." % profiler)


if __name__ == '__main__':
    fire.Fire(profile)
    print('Profile complete.')
