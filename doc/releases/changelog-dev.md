:orphan:

# Release 0.19.0-dev (development release)

<h3>New features since last release</h3>

* A new transform, `qml.transforms.rot_to_zxz`, has been added that transforms all
  `qml.Rot` single-qubit rotation gates into the sequence `[RZ,RX,RZ]`.
  [(#1772)](https://github.com/PennyLaneAI/pennylane/pull/1772)

* A new transform, `@qml.batch_params`, has been added, that makes QNodes 
handle a batch dimension in trainable parameters.
[(#1710)](https://github.com/PennyLaneAI/pennylane/pull/1710)

This transform will create multiple circuits, one per batch dimension.
As a result, it is both simulator and hardware compatible.

```python
@qml.batch_params
@qml.beta.qnode(dev)
def circuit(x, weights):
    qml.RX(x, wires=0)
    qml.RY(0.2, wires=1)
    qml.templates.StronglyEntanglingLayers(weights, wires=[0, 1, 2])
    return qml.expval(qml.Hadamard(0))
```

The `qml.batch_params` decorator allows us to pass arguments `x` and `weights`
that have a batch dimension. For example,

```pycon
>>> batch_size = 3
>>> x = np.linspace(0.1, 0.5, batch_size)
>>> weights = np.random.random((batch_size, 10, 3, 3))
```

If we evaluate the QNode with these inputs, we will get an output
of shape ``(batch_size,)``:

```pycon
>>> circuit(x, weights)
[-0.30773348  0.23135516  0.13086565]
```

* The new `qml.fourier.qnode_spectrum` function extends the former
  `qml.fourier.spectrum` function
  and takes classical processing of QNode arguments into account.
  The frequencies are computed per (requested) QNode argument instead
  of per gate `id`. The gate `id`s are ignored.
  [(#1681)](https://github.com/PennyLaneAI/pennylane/pull/1681)
  [(#1720)](https://github.com/PennyLaneAI/pennylane/pull/1720)

  Consider the following example, which uses non-trainable inputs `x`, `y` and `z`
  as well as trainable parameters `w` as arguments to the QNode.

  ```python
  import pennylane as qml
  import numpy as np

  n_qubits = 3
  dev = qml.device("default.qubit", wires=n_qubits)

  @qml.qnode(dev)
  def circuit(x, y, z, w):
      for i in range(n_qubits):
          qml.RX(0.5*x[i], wires=i)
          qml.Rot(w[0,i,0], w[0,i,1], w[0,i,2], wires=i)
          qml.RY(2.3*y[i], wires=i)
          qml.Rot(w[1,i,0], w[1,i,1], w[1,i,2], wires=i)
          qml.RX(z, wires=i)
      return qml.expval(qml.PauliZ(wires=0))

  x = np.array([1., 2., 3.])
  y = np.array([0.1, 0.3, 0.5])
  z = -1.8
  w = np.random.random((2, n_qubits, 3))
  ```

  This circuit looks as follows:

  ```pycon
  >>> print(qml.draw(circuit)(x, y, z, w))
  0: ──RX(0.5)──Rot(0.598, 0.949, 0.346)───RY(0.23)──Rot(0.693, 0.0738, 0.246)──RX(-1.8)──┤ ⟨Z⟩
  1: ──RX(1)────Rot(0.0711, 0.701, 0.445)──RY(0.69)──Rot(0.32, 0.0482, 0.437)───RX(-1.8)──┤
  2: ──RX(1.5)──Rot(0.401, 0.0795, 0.731)──RY(1.15)──Rot(0.756, 0.38, 0.38)─────RX(-1.8)──┤
  ```

  Applying the `qml.fourier.qnode_spectrum` function to the circuit for the non-trainable
  parameters, we obtain:

  ```pycon
  >>> spec = qml.fourier.qnode_spectrum(circuit, encoding_args={"x", "y", "z"})(x, y, z, w)
  >>> for inp, freqs in spec.items():
  ...     print(f"{inp}: {freqs}")
  "x": {(0,): [-0.5, 0.0, 0.5], (1,): [-0.5, 0.0, 0.5], (2,): [-0.5, 0.0, 0.5]}
  "y": {(0,): [-2.3, 0.0, 2.3], (1,): [-2.3, 0.0, 2.3], (2,): [-2.3, 0.0, 2.3]}
  "z": {(): [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0]}
  ```

  We can see that all three parameters in the QNode arguments ``x`` and ``y``
  contribute the spectrum of a Pauli rotation ``[-1.0, 0.0, 1.0]``, rescaled with the
  prefactor of the respective parameter in the circuit.
  The three ``RX`` rotations using the parameter ``z`` accumulate, yielding a more
  complex frequency spectrum.

  For details on how to control for which parameters the spectrum is computed,
  a comparison to `qml.fourier.circuit_spectrum`, and other usage details, please see the
  [fourier.qnode_spectrum docstring](https://pennylane.readthedocs.io/en/latest/code/api/pennylane.fourier.qnode_spectrum.html).

* There is a new utility function `qml.math.is_independent` that checks whether
  a callable is independent of its arguments.
  [(#1700)](https://github.com/PennyLaneAI/pennylane/pull/1700)

  **Warning**

  This function is experimental and might behave differently than expected.
  Also, it might be subject to change.

  **Disclaimer**

  Note that the test relies on both numerical and analytical checks, except
  when using the PyTorch interface which only performs a numerical check.
  It is known that there are edge cases on which this test will yield wrong
  results, in particular non-smooth functions may be problematic.
  For details, please refer to the
  [is_indpendent docstring](https://pennylane.readthedocs.io/en/latest/code/api/pennylane.math.is_independent.html).

* Support for differentiable execution of batches of circuits has been
  extended to the JAX interface for scalar functions, via the beta
  `pennylane.interfaces.batch` module.
  [(#1634)](https://github.com/PennyLaneAI/pennylane/pull/1634)

  For example using the `execute` function from the `pennylane.interfaces.batch` module:

  ```python
  from pennylane.interfaces.batch import execute

  def cost_fn(x):
      with qml.tape.JacobianTape() as tape1:
          qml.RX(x[0], wires=[0])
          qml.RY(x[1], wires=[1])
          qml.CNOT(wires=[0, 1])
          qml.var(qml.PauliZ(0) @ qml.PauliX(1))

      with qml.tape.JacobianTape() as tape2:
          qml.RX(x[0], wires=0)
          qml.RY(x[0], wires=1)
          qml.CNOT(wires=[0, 1])
          qml.probs(wires=1)

      result = execute(
        [tape1, tape2], dev,
        gradient_fn=qml.gradients.param_shift,
        interface="autograd"
      )
      return (result[0] + result[1][0, 0])[0]

  res = jax.grad(cost_fn)(params)
  ```

* The unitary matrix corresponding to a quantum circuit can now be created using the new
  `get_unitary_matrix()` transform.
  [(#1609)](https://github.com/PennyLaneAI/pennylane/pull/1609)

* Arbitrary two-qubit unitaries can now be decomposed into elementary gates. This
  functionality has been incorporated into the `qml.transforms.unitary_to_rot` transform, and is
  available separately as `qml.transforms.two_qubit_decomposition`.
  [(#1552)](https://github.com/PennyLaneAI/pennylane/pull/1552)

  As an example, consider the following randomly-generated matrix and circuit that uses it:

  ```python
  U = np.array([
      [-0.03053706-0.03662692j,  0.01313778+0.38162226j, 0.4101526 -0.81893687j, -0.03864617+0.10743148j],
      [-0.17171136-0.24851809j,  0.06046239+0.1929145j, -0.04813084-0.01748555j, -0.29544883-0.88202604j],
      [ 0.39634931-0.78959795j, -0.25521689-0.17045233j, -0.1391033 -0.09670952j, -0.25043606+0.18393466j],
      [ 0.29599198-0.19573188j,  0.55605806+0.64025769j, 0.06140516+0.35499559j,  0.02674726+0.1563311j ]
  ])

  dev = qml.device('default.qubit', wires=2)

  @qml.qnode(dev)
  @qml.transforms.unitary_to_rot
  def circuit(x, y):
      qml.RX(x, wires=0)
      qml.QubitUnitary(U, wires=[0, 1])
      qml.RY(y, wires=0)
      return qml.expval(qml.PauliZ(wires=0))
  ```

  If we run the circuit, we can see the new decomposition:

  ```pycon
  >>> circuit(0.3, 0.4)
  tensor(-0.70520073, requires_grad=True)
  >>> print(qml.draw(circuit)(0.3, 0.4))
  0: ──RX(0.3)─────────────────Rot(-3.5, 0.242, 0.86)──╭X──RZ(0.176)───╭C─────────────╭X──Rot(5.56, 0.321, -2.09)───RY(0.4)──┤ ⟨Z⟩
  1: ──Rot(-1.64, 2.69, 1.58)──────────────────────────╰C──RY(-0.883)──╰X──RY(-1.47)──╰C──Rot(-1.46, 0.337, 0.587)───────────┤
  ```

* The transform for the Jacobian of the classical preprocessing within a QNode,
  `qml.transforms.classical_jacobian`, now takes a keyword argument `argnum` to specify
  the QNode argument indices with respect to which the Jacobian is computed.
  [(#1645)](https://github.com/PennyLaneAI/pennylane/pull/1645)

  An example for the usage of ``argnum`` is

  ```python
  @qml.qnode(dev)
  def circuit(x, y, z):
      qml.RX(qml.math.sin(x), wires=0)
      qml.CNOT(wires=[0, 1])
      qml.RY(y ** 2, wires=1)
      qml.RZ(1 / z, wires=1)
      return qml.expval(qml.PauliZ(0))

  jac_fn = qml.transforms.classical_jacobian(circuit, argnum=[1, 2])
  ```

  The Jacobian can then be computed at specified parameters.

  ```pycon
  >>> x, y, z = np.array([0.1, -2.5, 0.71])
  >>> jac_fn(x, y, z)
  (array([-0., -5., -0.]), array([-0.        , -0.        , -1.98373339]))
  ```

  The returned arrays are the derivatives of the three parametrized gates in the circuit
  with respect to `y` and `z` respectively.

  There also are explicit tests for `classical_jacobian` now, which previously was tested
  implicitly via its use in the `metric_tensor` transform.

  For more usage details, please see the
  [classical Jacobian docstring](https://pennylane.readthedocs.io/en/latest/code/api/pennylane.transforms.classical_jacobian.html).

* Added a new operation `OrbitalRotation`, which implements the spin-adapted spatial orbital rotation gate.
  [(#1665)](https://github.com/PennyLaneAI/pennylane/pull/1665)

  An example circuit that uses `OrbitalRotation` operation is:

  ```python
  dev = qml.device('default.qubit', wires=4)
  @qml.qnode(dev)
  def circuit(phi):
      qml.BasisState(np.array([1, 1, 0, 0]), wires=[0, 1, 2, 3])
      qml.OrbitalRotation(phi, wires=[0, 1, 2, 3])
      return qml.state()
  ```

  If we run this circuit, we will get the following output

  ```pycon
  >>> circuit(0.1)
  array([ 0.        +0.j,  0.        +0.j,  0.        +0.j,
          0.00249792+0.j,  0.        +0.j,  0.        +0.j,
          -0.04991671+0.j,  0.        +0.j,  0.        +0.j,
          -0.04991671+0.j,  0.        +0.j,  0.        +0.j,
          0.99750208+0.j,  0.        +0.j,  0.        +0.j,
          0.        +0.j])
  ```

* A new, experimental QNode has been added, that adds support for batch execution of circuits,
  custom quantum gradient support, and arbitrary order derivatives. This QNode is available via
  `qml.beta.QNode`, and `@qml.beta.qnode`.
  [(#1642)](https://github.com/PennyLaneAI/pennylane/pull/1642)
  [(#1646)](https://github.com/PennyLaneAI/pennylane/pull/1646)
  [(#1651)](https://github.com/PennyLaneAI/pennylane/pull/1651)

  It differs from the standard QNode in several ways:

  - Custom gradient transforms can be specified as the differentiation method:

    ```python
    @qml.gradients.gradient_transform
    def my_gradient_transform(tape):
        ...
        return tapes, processing_fn

    @qml.beta.qnode(dev, diff_method=my_gradient_transform)
    def circuit():
    ```

  - Arbitrary :math:`n`-th order derivatives are supported on hardware using
    gradient transforms such as the parameter-shift rule. To specify that an :math:`n`-th
    order derivative of a QNode will be computed, the `max_diff` argument should be set.
    By default, this is set to 1 (first-order derivatives only).

  - Internally, if multiple circuits are generated for execution simultaneously, they
    will be packaged into a single job for execution on the device. This can lead to
    significant performance improvement when executing the QNode on remote
    quantum hardware.

  - When decomposing the circuit, the default decomposition strategy will prioritize
    decompositions that result in the smallest number of parametrized operations
    required to satisfy the differentiation method. Additional decompositions required
    to satisfy the native gate set of the quantum device will be performed later, by the
    device at execution time. While this may lead to a slight increase in classical processing,
    it significantly reduces the number of circuit evaluations needed to compute
    gradients of complex unitaries.

  In an upcoming release, this QNode will replace the existing one. If you come across any bugs
  while using this QNode, please let us know via a [bug
  report](https://github.com/PennyLaneAI/pennylane/issues/new?assignees=&labels=bug+%3Abug%3A&template=bug_report.yml&title=%5BBUG%5D)
  on our GitHub bug tracker.

  Currently, this beta QNode does not support the following features:

  - Non-mutability via the `mutable` keyword argument
  - Viewing specifications with `qml.specs`
  - The `reversible` QNode differentiation method
  - The ability to specify a `dtype` when using PyTorch and TensorFlow.

  It is also not tested with the `qml.qnn` module.

* Two new methods were added to the Device API, allowing PennyLane devices
  increased control over circuit decompositions.
  [(#1651)](https://github.com/PennyLaneAI/pennylane/pull/1651)

  - `Device.expand_fn(tape) -> tape`: expands a tape such that it is supported by the device. By
    default, performs the standard device-specific gate set decomposition done in the default
    QNode. Devices may overwrite this method in order to define their own decomposition logic.

    Note that the numerical result after applying this method should remain unchanged; PennyLane
    will assume that the expanded tape returns exactly the same value as the original tape when
    executed.

  - `Device.batch_transform(tape) -> (tapes, processing_fn)`: preprocesses the tape in the case
    where the device needs to generate multiple circuits to execute from the input circuit. The
    requirement of a post-processing function makes this distinct to the `expand_fn` method above.

    By default, this method applies the transform

    .. math:: \left\langle \sum_i c_i h_i\right\rangle -> \sum_i c_i \left\langle h_i \right\rangle

    if `expval(H)` is present on devices that do not natively support Hamiltonians with
    non-commuting terms.

* Added a new template `GateFabric`, which implements a local, expressive, quantum-number-preserving
  ansatz proposed by Anselmetti *et al.* in [arXiv:2104.05692](https://arxiv.org/abs/2104.05695).
  [(#1687)](https://github.com/PennyLaneAI/pennylane/pull/1687)

  An example of a circuit using `GateFabric` template is:

  ```python
  coordinates = np.array([0.0, 0.0, -0.6614, 0.0, 0.0, 0.6614])
  H, qubits = qml.qchem.molecular_hamiltonian(["H", "H"], coordinates)
  ref_state = qml.qchem.hf_state(electrons=2, qubits)

  dev = qml.device('default.qubit', wires=qubits)
  @qml.qnode(dev)
  def ansatz(weights):
      qml.templates.GateFabric(weights, wires=[0,1,2,3],
                                  init_state=ref_state, include_pi=True)
      return qml.expval(H)
  ```

  For more details, see the [GateFabric documentation](../code/api/pennylane.templates.layers.GateFabric.html).


<h3>Improvements</h3>

* `qml.probs` now accepts an attribute `op` that allows to rotate the computational basis and get the 
  probabilities in the rotated basis.
  [(#1692)](https://github.com/PennyLaneAI/pennylane/pull/1692)
  
* The `qml.beta.QNode` now supports the `qml.qnn` module.
  [(#1748)](https://github.com/PennyLaneAI/pennylane/pull/1748)

* `@qml.beta.QNode` now supports the `qml.specs` transform.
  [(#1739)](https://github.com/PennyLaneAI/pennylane/pull/1739)

* `qml.circuit_drawer.drawable_layers` and `qml.circuit_drawer.drawable_grid` process a list of
  operations to layer positions for drawing.
  [(#1639)](https://github.com/PennyLaneAI/pennylane/pull/1639)

* `qml.transforms.batch_transform` now accepts `expand_fn`s that take additional arguments and
  keyword arguments. In fact, `expand_fn` and `transform_fn` now **must** have the same signature.
  [(#1721)](https://github.com/PennyLaneAI/pennylane/pull/1721)

* The `qml.batch_transform` decorator is now ignored during Sphinx builds, allowing
  the correct signature to display in the built documentation.
  [(#1733)](https://github.com/PennyLaneAI/pennylane/pull/1733)

* The use of `expval(H)`, where `H` is a cost Hamiltonian generated by the `qaoa` module,
  has been sped up. This was achieved by making PennyLane decompose a circuit with an `expval(H)`
  measurement into subcircuits if the `Hamiltonian.grouping_indices` attribute is set, and setting
  this attribute in the relevant `qaoa` module functions.
  [(#1718)](https://github.com/PennyLaneAI/pennylane/pull/1718)

* The tests for qubit operations are split into multiple files.
  [(#1661)](https://github.com/PennyLaneAI/pennylane/pull/1661)

* The `qml.metric_tensor` transform has been improved with regards to
  both function and performance.
  [(#1638)](https://github.com/PennyLaneAI/pennylane/pull/1638)
  [(#1721)](https://github.com/PennyLaneAI/pennylane/pull/1721)

  - If the underlying device supports batch execution of circuits, the quantum circuits required to
    compute the metric tensor elements will be automatically submitted as a batched job. This can
    lead to significant performance improvements for devices with a non-trivial job submission
    overhead.

  - Previously, the transform would only return the metric tensor with respect to gate arguments,
    and ignore any classical processing inside the QNode, even very trivial classical processing
    such as parameter permutation. The metric tensor now takes into account classical processing,
    and returns the metric tensor with respect to QNode arguments, not simply gate arguments:

    ```pycon
    >>> @qml.qnode(dev)
    ... def circuit(x):
    ...     qml.Hadamard(wires=1)
    ...     qml.RX(x[0], wires=0)
    ...     qml.CNOT(wires=[0, 1])
    ...     qml.RY(x[1] ** 2, wires=1)
    ...     qml.RY(x[1], wires=0)
    ...     return qml.expval(qml.PauliZ(0))
    >>> x = np.array([0.1, 0.2], requires_grad=True)
    >>> qml.metric_tensor(circuit)(x)
    array([[0.25      , 0.        ],
           [0.        , 0.28750832]])
    ```

    To revert to the previous behaviour of returning the metric tensor with respect to gate
    arguments, `qml.metric_tensor(qnode, hybrid=False)` can be passed.

    ```pycon
    >>> qml.metric_tensor(circuit, hybrid=False)(x)
    array([[0.25      , 0.        , 0.        ],
           [0.        , 0.25      , 0.        ],
           [0.        , 0.        , 0.24750832]])
    ```

  - The metric tensor transform now works with a larger set of operations. In particular,
    all operations that have a single variational parameter and define a generator are now
    supported. In addition to a reduction in decomposition overhead, the change
    also results in fewer circuit evaluations.


* ``qml.circuit_drawer.CircuitDrawer`` can accept a string for the ``charset`` keyword, instead of a ``CharSet`` object.
  [(#1640)](https://github.com/PennyLaneAI/pennylane/pull/1640)

* ``qml.math.sort`` will now return only the sorted torch tensor and not the corresponding indices, making sort consistent across interfaces.
    [(#1691)](https://github.com/PennyLaneAI/pennylane/pull/1691)

* Operations can now have gradient recipes that depend on the state of the operation.
  [(#1674)](https://github.com/PennyLaneAI/pennylane/pull/1674)

  For example, this allows for gradient recipes that are parameter dependent:

  ```python
  class RX(qml.RX):

      @property
      def grad_recipe(self):
          # The gradient is given by [f(2x) - f(0)] / (2 sin(x)), by subsituting
          # shift = x into the two term parameter-shift rule.
          x = self.data[0]
          c = 0.5 / np.sin(x)
          return ([[c, 0.0, 2 * x], [-c, 0.0, 0.0]],)
  ```

* Shots can now be passed as a runtime argument to transforms that execute circuits in batches, similarly
  to QNodes.
  [(#1707)](https://github.com/PennyLaneAI/pennylane/pull/1707)

  An example of such a transform are the gradient transforms in the
  `qml.gradients` module. As a result, we can now call gradient transforms
  (such as `qml.gradients.param_shift`) and set the number of shots at runtime.

  ```pycon
  >>> dev = qml.device("default.qubit", wires=1, shots=1000)
  >>> @qml.beta.qnode(dev)
  ... def circuit(x):
  ...     qml.RX(x, wires=0)
  ...     return qml.expval(qml.PauliZ(0))
  >>> grad_fn = qml.gradients.param_shift(circuit)
  >>> grad_fn(0.564, shots=[(1, 10)]).T
  array([[-1., -1., -1., -1., -1.,  0., -1.,  0., -1.,  0.]])
  >>> grad_fn(0.1233, shots=None)
  array([[-0.53457096]])
  ```

* Specific QNode execution options are now re-used by batch transforms
  to execute transformed QNodes.
  [(#1708)](https://github.com/PennyLaneAI/pennylane/pull/1708)

<h3>Breaking changes</h3>

- The input signature of an `expand_fn` used in a `batch_transform`
  now **must** have the same signature as the provided `transform_fn`,
  and vice versa.
  [(#1721)](https://github.com/PennyLaneAI/pennylane/pull/1721)

- The expansion rule in the `qml.metric_tensor` transform has been changed.
  [(#1721)](https://github.com/PennyLaneAI/pennylane/pull/1721)

  If `hybrid=False`, the changed expansion rule might lead to a changed output.

- The `qml.metric_tensor` keyword argument `diag_approx` is deprecated.
  Approximations can be controlled with the more fine-grained `approx`
  keyword argument, with `approx="block-diag"` (the default) reproducing
  the old behaviour.
  [(#1721)](https://github.com/PennyLaneAI/pennylane/pull/1721)

* The `default.qubit.torch` device automatically determines if computations
  should be run on a CPU or a GPU and doesn't take a `torch_device` argument
  anymore.
  [(#1705)](https://github.com/PennyLaneAI/pennylane/pull/1705)

* The `QNode.metric_tensor` method has been deprecated, and will be removed in an upcoming release.
  Please use the `qml.metric_tensor` transform instead.
  [(#1638)](https://github.com/PennyLaneAI/pennylane/pull/1638)

* The utility function `qml.math.requires_grad` now returns `True` when using Autograd
  if and only if the `requires_grad=True` attribute is set on the NumPy array. Previously,
  this function would return `True` for *all* NumPy arrays and Python floats, unless
  `requires_grad=False` was explicitly set.
  [(#1638)](https://github.com/PennyLaneAI/pennylane/pull/1638)

- The operation `qml.Interferometer` has been renamed `qml.InterferometerUnitary` in order to
  distinguish it from the template `qml.templates.Interferometer`.
  [(#1714)](https://github.com/PennyLaneAI/pennylane/pull/1714)

<h3>Deprecations</h3>

* The `qml.fourier.spectrum` function has been renamed to `qml.fourier.circuit_spectrum`,
  in order to clearly separate the new `qnode_spectrum` function from this one.
  `qml.fourier.spectrum` is now an alias for `circuit_spectrum` but is flagged for
  deprecation and will be removed soon.
  [(#1681)](https://github.com/PennyLaneAI/pennylane/pull/1681)

* The `init` module, which contains functions to generate random parameter tensors for
  templates, is flagged for deprecation and will be removed in the next release cycle.
  Instead, the templates' `shape` method can be used to get the desired shape of the tensor,
  which can then be generated manually.
  [(#1689)](https://github.com/PennyLaneAI/pennylane/pull/1689)

<h3>Bug fixes</h3>

* Fixes a bug where the GPU cannot be used with `qml.qnn.TorchLayer`.
  [(#1705)](https://github.com/PennyLaneAI/pennylane/pull/1705)

* Fix a bug where the devices cache the same result for different observables return types.
  [(#1719)](https://github.com/PennyLaneAI/pennylane/pull/1719)

* Fixed a bug of the default circuit drawer where having more measurements
  compared to the number of measurements on any wire raised a `KeyError`.
  [(#1702)](https://github.com/PennyLaneAI/pennylane/pull/1702)

* Fix a bug where it was not possible to use `jax.jit` on a `QNode` when using `QubitStateVector`.
  [(#1683)](https://github.com/PennyLaneAI/pennylane/pull/1683)

* The device suite tests can now execute successfully if no shots configuration variable is given.
  [(#1641)](https://github.com/PennyLaneAI/pennylane/pull/1641)

* Fixes a bug where the `qml.gradients.param_shift` transform would raise an error while attempting
  to compute the variance of a QNode with ragged output.
  [(#1646)](https://github.com/PennyLaneAI/pennylane/pull/1646)

* Fixes a bug in `default.mixed`, to ensure that returned probabilities are always non-negative.
  [(#1680)](https://github.com/PennyLaneAI/pennylane/pull/1680)

* Fixes a bug where gradient transforms would fail to apply to QNodes
  containing classical processing.
  [(#1699)](https://github.com/PennyLaneAI/pennylane/pull/1699)

<h3>Documentation</h3>

* Adds a link to https://pennylane.ai/qml/demonstrations.html in the navbar.
  [(#1624)](https://github.com/PennyLaneAI/pennylane/pull/1624)

* Corrects the docstring of `ExpvalCost` by adding `wires` to the signature of the `ansatz` argument. [(#1715)](https://github.com/PennyLaneAI/pennylane/pull/1715)

* All instances of `qnode.draw()` have been updated to instead use the transform `qml.draw(qnode)`.
  [(#1750)](https://github.com/PennyLaneAI/pennylane/pull/1750)

<h3>Contributors</h3>

This release contains contributions from (in alphabetical order):

Utkarsh Azad, Akash Narayanan B, Olivia Di Matteo, Samuele Ferracin, Andrew Gardhouse, Josh Izaac, Christina Lee,
Romain Moyard, Carrie-Anne Rubidge, Maria Schuld, Ingrid Strandberg, Antal Száva, Cody Wang,
David Wierichs.
