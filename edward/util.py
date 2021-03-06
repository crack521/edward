import tensorflow as tf
import numpy as np

def cumprod(xs):
    """
    Cumulative product of a tensor along first dimension.
    https://github.com/tensorflow/tensorflow/issues/813
    """
    values = tf.unpack(xs)
    out = []
    prev = tf.ones_like(values[0])
    for val in values:
        s = prev * val
        out.append(s)
        prev = s

    result = tf.pack(out)
    return result

def digamma(x):
    """
    Computes the digamma function element-wise.

    TensorFlow doesn't have special functions with support for
    automatic differentiation, so use a log/exp/polynomial
    approximation.
    http://www.machinedlearnings.com/2011/06/faster-lda.html

    Parameters
    ----------
    x : np.array or tf.Tensor
        scalar, vector, or rank-n tensor

    Returns
    -------
    tf.Tensor
        size corresponding to size of input
    """
    twopx = 2.0 + x
    logterm = tf.log(twopx)
    return - (1.0 + 2.0 * x) / (x * (1.0 + x)) - \
           (13.0 + 6.0 * x) / (12.0 * twopx * twopx) + logterm

def dot(x, y):
    """
    x is M x N matrix and y is N-vector, or
    x is M-vector and y is M x N matrix
    """
    if len(x.get_shape()) == 1:
        vec = x
        mat = y
        return tf.matmul(tf.expand_dims(vec, 0), mat)
    else:
        mat = x
        vec = y
        return tf.matmul(mat, tf.expand_dims(vec, 1))

def get_dims(x):
    """
    Get values of each dimension.

    Arguments
    ----------
    x: tensor scalar or array
    """
    dims = x.get_shape()
    if len(dims) == 0: # scalar
        return [1]
    else: # array
        return [dim.value for dim in dims]

def get_session():
    """Get the session defined globally; if not already defined, then
    the function will create a global session."""
    global _ED_SESSION
    if tf.get_default_session() is None:
        _ED_SESSION = tf.InteractiveSession()

    return _ED_SESSION

def hessian(y, xs):
    """
    Calculate Hessian of y with respect to each x in xs.

    Parameters
    ----------
    y : tf.Tensor
        Tensor to calculate Hessian of.
    xs : list
        List of TensorFlow variables to calculate with respect to.
        The variables can have different shapes.
    """
    # Calculate flattened vector grad_{xs} y.
    grads = tf.gradients(y, xs)
    grads = [tf.reshape(grad, [-1]) for grad in grads]
    grads = tf.concat(0, grads)
    # Loop over each element in the vector.
    mat = []
    d = grads.get_shape()[0]
    for j in range(d):
        # Calculate grad_{xs} ( [ grad_{xs} y ]_j ).
        gradjgrads = tf.gradients(grads[j], xs)
        # Flatten into vector.
        hi = []
        for l in range(len(xs)):
            hij = gradjgrads[l]
            # return 0 if gradient doesn't exist; TensorFlow returns None
            if hij is None:
                hij = tf.zeros(xs[l].get_shape(), dtype=tf.float32)

            hij = tf.reshape(hij, [-1])
            hi.append(hij)

        hi = tf.concat(0, hi)
        mat.append(hi)

    # Form matrix where each row is grad_{xs} ( [ grad_{xs} y ]_j ).
    return tf.pack(mat)

def kl_multivariate_normal(loc_one, scale_one, loc_two=0, scale_two=1):
    """
    Calculates the KL of multivariate normal distributions with
    diagonal covariances.

    Parameters
    ----------
    loc_one : tf.Tensor
        n-dimensional vector, or M x n-dimensional matrix where each
        row represents the mean of a n-dimensional Gaussian
    scale_one : tf.Tensor
        n-dimensional vector, or M x n-dimensional matrix where each
        row represents the standard deviation of a n-dimensional Gaussian
    loc_two : tf.Tensor, optional
        n-dimensional vector, or M x n-dimensional matrix where each
        row represents the mean of a n-dimensional Gaussian
    scale_two : tf.Tensor, optional
        n-dimensional vector, or M x n-dimensional matrix where each
        row represents the standard deviation of a n-dimensional Gaussian

    Returns
    -------
    tf.Tensor
        for scalar or vector inputs, outputs the scalar
            KL( N(z; loc_one, scale_one) || N(z; loc_two, scale_two) )
        for matrix inputs, outputs the vector
            [KL( N(z; loc_one[m,:], scale_one[m,:]) ||
                 N(z; loc_two[m,:], scale_two[m,:]) )]_{m=1}^M
    """
    if loc_two == 0 and scale_two == 1:
        return 0.5 * tf.reduce_sum(
            tf.square(scale_one) + tf.square(loc_one) - \
            1.0 - 2.0 * tf.log(scale_one))
    else:
        return 0.5 * tf.reduce_sum(
            tf.square(scale_one/scale_two) + \
            tf.square((loc_two - loc_one)/scale_two) - \
            1.0 + 2.0 * tf.log(scale_two) - 2.0 * tf.log(scale_one), 1)

def lbeta(x):
    """
    Computes the log of Beta(x), reducing along the last dimension.

    TensorFlow doesn't have special functions with support for
    automatic differentiation, so use a log/exp/polynomial
    approximation.
    http://www.machinedlearnings.com/2011/06/faster-lda.html

    Parameters
    ----------
    x : np.array or tf.Tensor
        vector or rank-n tensor

    Returns
    -------
    tf.Tensor
        scalar if vector input, rank-(n-1) if rank-n tensor input
    """
    x = tf.cast(tf.squeeze(x), dtype=tf.float32)
    if len(get_dims(x)) == 1:
        return tf.reduce_sum(lgamma(x)) - lgamma(tf.reduce_sum(x))
    else:
        return tf.reduce_sum(lgamma(x), 1) - lgamma(tf.reduce_sum(x, 1))

def lgamma(x):
    """
    Computes the log of Gamma(x) element-wise.

    TensorFlow doesn't have special functions with support for
    automatic differentiation, so use a log/exp/polynomial
    approximation.
    http://www.machinedlearnings.com/2011/06/faster-lda.html

    Parameters
    ----------
    x : np.array or tf.Tensor
        scalar, vector, or rank-n tensor

    Returns
    -------
    tf.Tensor
        size corresponding to size of input
    """
    logterm = tf.log(x * (1.0 + x) * (2.0 + x))
    xp3 = 3.0 + x
    return -2.081061466 - x + 0.0833333 / xp3 - logterm + (2.5 + x) * tf.log(xp3)

def log_sum_exp(x):
    """
    Computes the log_sum_exp of the elements in x.

    Works for x with
        shape=TensorShape([Dimension(N)])
        shape=TensorShape([Dimension(N), Dimension(1)])

    Not tested for anything beyond that.
    """
    x_max = tf.reduce_max(x)
    return tf.add(x_max, tf.log(tf.reduce_sum(tf.exp(tf.sub(x, x_max)))))

def logit(x):
    """log(x / (1 - x))"""
    x = tf.clip_by_value(x, 1e-8, 1.0 - 1e-8)
    return tf.log(x) - tf.log(1.0 - x)

def multivariate_rbf(x, y=0.0, sigma=1.0, l=1.0):
    """
    Squared-exponential kernel
    k(x, y) = sigma^2 exp{ -1/(2l^2) sum_i (x_i - y_i)^2 }
    """
    return tf.pow(sigma, 2.0) * \
           tf.exp(-1.0/(2.0*tf.pow(l, 2.0)) * \
                  tf.reduce_sum(tf.pow(x - y , 2.0)))

def rbf(x, y=0.0, sigma=1.0, l=1.0):
    """
    Squared-exponential kernel element-wise
    k(x, y) = sigma^2 exp{ -1/(2l^2) (x_i - y_i)^2 }
    """
    return tf.pow(sigma, 2.0) * \
           tf.exp(-1.0/(2.0*tf.pow(l, 2.0)) * tf.pow(x - y , 2.0))

def set_seed(x):
    """
    Set seed for both NumPy and TensorFlow.
    """
    np.random.seed(x)
    tf.set_random_seed(x)

def softplus(x):
    """
    Softplus. TensorFlow can't currently autodiff through
    tf.nn.softplus().
    """
    return tf.log(1.0 + tf.exp(x))
