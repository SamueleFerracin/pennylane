# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Contains the classical Jacobian transform.
"""
# pylint: disable=import-outside-toplevel
import pennylane as qml
from pennylane import numpy as np


def classical_jacobian(qnode, argnum=None):
    r"""Returns a function to extract the Jacobian
    matrix of the classical part of a QNode.

    This transform allows the classical dependence between the QNode
    arguments and the quantum gate arguments to be extracted.

    Args:
        qnode (.QNode): QNode to compute the (classical) Jacobian of
        argnum (int or Sequence[int]): indices of QNode arguments with respect to which
            the (classical) Jacobian is computed

    Returns:
        function: Function which accepts the same arguments as the QNode.
        When called, this function will return the Jacobian of the QNode
        gate arguments with respect to the QNode arguments indexed by ``argnum``.

    **Example**

    Consider the following QNode:

    >>> @qml.qnode(dev)
    ... def circuit(weights):
    ...     qml.RX(weights[0], wires=0)
    ...     qml.RY(0.2 * weights[0], wires=1)
    ...     qml.RY(2.5, wires=0)
    ...     qml.RZ(weights[1] ** 2, wires=1)
    ...     qml.RX(weights[2], wires=1)
    ...     return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))

    We can use this transform to extract the relationship :math:`f: \mathbb{R}^n \rightarrow
    \mathbb{R}^m` between the input QNode arguments :math:`w` and the gate arguments :math:`g`, for
    a given value of the QNode arguments:

    >>> cjac_fn = qml.transforms.classical_jacobian(circuit)
    >>> weights = np.array([1., 1., 0.6], requires_grad=True)
    >>> cjac = cjac_fn(weights)
    >>> print(cjac)
    [[1.  0.  0. ]
     [0.2 0.  0. ]
     [0.  0.  0. ]
     [0.  1.2 0. ]
     [0.  0.  1. ]]

    The returned Jacobian has rows corresponding to gate arguments, and columns
    corresponding to QNode arguments; that is,

    .. math:: J_{ij} = \frac{\partial}{\partial g_i} f(w_j).

    We can see that:

    - The zeroth element of ``weights`` is repeated on the first two gates generated by the QNode.

    - The third row consisting of all zeros indicates that the third gate ``RY(2.5)`` does not
      depend on the ``weights``.

    - The quadratic dependence of the fourth gate argument yields :math:`2\cdot 0.6=1.2`.

    .. note::

        The QNode is constructed during this operation.

    For a QNode with multiple QNode arguments, the arguments with respect to which the
    Jacobian is computed can be controlled with the ``argnum`` keyword argument.
    The output for ``argnum=None`` depends on the backend:

    .. list-table:: Output format of ``classical_jacobian``
       :widths: 25 25 25 25
       :header-rows: 1

       * - Interface
         - ``argnum=None``
         - ``type(argnum)=int``
         - ``argnum=Sequence[int]``
       * - ``'autograd'``
         - ``tuple(arrays)`` [1]
         - ``array``
         - ``tuple(array)``
       * - ``'jax'``
         - ``array``
         - ``array``
         - ``tuple(array)``
       * - ``'tf'``
         - ``tuple(arrays)``
         - ``array``
         - ``tuple(array)``
       * - ``'torch'``
         - ``tuple(arrays)``
         - ``array``
         - ``tuple(array)``

    [1] If all QNode argument are scalars, the tuple is unpacked and the one-dimensional Jacobian
    arrays are stacked into one ``array``. If there only is one QNode argument, the tuple is
    unpacked as well. Both is due to the behaviour of ``qml.jacobian``.

    **Example with ``argnum``**

    >>> @qml.qnode(dev)
    ... def circuit(x, y, z):
    ...     qml.RX(qml.math.sin(x), wires=0)
    ...     qml.CNOT(wires=[0, 1])
    ...     qml.RY(y ** 2, wires=1)
    ...     qml.RZ(1 / z, wires=1)
    ...     return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))
    >>> jac_fn = qml.transforms.classical_jacobian(circuit, argnum=[1, 2])
    >>> x, y, z = np.array([0.1, -2.5, 0.71])
    >>> jac_fn(x, y, z)
    (array([-0., -5., -0.]), array([-0.        , -0.        , -1.98373339]))

    Only the Jacobians with respect to the arguments ``x`` and ``y`` were computed, and
    returned as a tuple of ``arrays``.

    """

    def classical_preprocessing(*args, **kwargs):
        """Returns the trainable gate parameters for a given QNode input."""
        trainable_only = kwargs.pop("_trainable_only", True)
        qnode.construct(args, kwargs)
        return qml.math.stack(qnode.qtape.get_parameters(trainable_only=trainable_only))

    if qnode.interface == "autograd":

        def _jacobian(*args, **kwargs):
            if argnum is None:
                jac = qml.jacobian(classical_preprocessing)(*args, **kwargs)
            elif np.isscalar(argnum):
                jac = qml.jacobian(classical_preprocessing, argnum=argnum)(*args, **kwargs)
            else:
                jac = tuple(
                    (
                        qml.jacobian(classical_preprocessing, argnum=i)(*args, **kwargs)
                        for i in argnum
                    )
                )
            return jac

        return _jacobian

    if qnode.interface == "torch":
        import torch

        def _jacobian(*args, **kwargs):  # pylint: disable=unused-argument
            jac = torch.autograd.functional.jacobian(classical_preprocessing, args)
            if argnum is not None:
                if np.isscalar(argnum):
                    jac = jac[argnum]
                else:
                    jac = tuple((jac[idx] for idx in argnum))
            return jac

        return _jacobian

    if qnode.interface == "jax":
        import jax

        argnum = 0 if argnum is None else argnum

        def _jacobian(*args, **kwargs):
            kwargs["_trainable_only"] = False
            return jax.jacobian(classical_preprocessing, argnums=argnum)(*args, **kwargs)

        return _jacobian

    if qnode.interface == "tf":
        import tensorflow as tf

        def _jacobian(*args, **kwargs):
            if np.isscalar(argnum):
                sub_args = args[argnum]
            elif argnum is None:
                sub_args = args
            else:
                sub_args = tuple((args[i] for i in argnum))

            with tf.GradientTape() as tape:
                gate_params = classical_preprocessing(*args, **kwargs)

            jac = tape.jacobian(gate_params, sub_args)
            return jac

        return _jacobian
