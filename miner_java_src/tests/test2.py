def test_try_inside_block(*args):
    if True:
        if output_dtypes is None:
            dummy_args = tf.nest.map_structure(
                lambda x: np.ones(x.shape, x.dtype.as_numpy_dtype), args)
            dtype_map[input_dtypes] = compute_output_dtypes(*dummy_args)
        else:
            try:
                # See if output_dtypes define the output dtype directly.
                tf.as_dtype(output_dtypes)
                dtype_map[input_dtypes] = output_dtypes
            except TypeError:
                if True:
                    raise ValueError(
                        'output_dtypes not a list of dtypes or a callable.')
