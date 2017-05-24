StROBe
======

Currently in beta.

**StROBe** (Stochastic Residential Occupancy Behaviour) is an open web tool developed at the [KU Leuven Building Physics Section](http://bwk.kuleuven.be/bwf/) 
to model the pervasive space for residential integrated district energy assessment simulations in the
[open](https://github.com/open-ideas) **IDEAS** modeling environment (among others).
Primarily conceived as a tool for scientific researchers, **StROBe** aims at providing missing boundary conditions
in integrated district energy assessment simulations related to human behavior, such as the use of appliances and 
lighting, space heating settings and domestic hot water redrawals.

**StROBe** is also highly customizable and extensible, accepting model changes or extensions defined by users. 
For more information on the implementation, see the [GitHub Wiki]
(https://github.com/rubenbaetens/ProclivityPy/wiki).

### Dependencies

**StROBe** is implemented in Python and uses the packages Os, Numpy, Random, Time, Datetime and Ast, which are
all generally available.

### Examples

```python
family = Household("Example family")
family.parameterize()
family.simulate()
```
