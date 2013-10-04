ProclivityPy
============

Currently in beta.

**ProclivityPy** is an open web tool developed at the [KU Leuven Building Physics Section](http://bwk.kuleuven.be/bwf/) 
to model the pervasive space for residential integrated district energy assessment simulations on the
[IDEAS.mo](https://github.com/open-ideas) modeling environment (and others).
Primarily conceived as a tool for scientific researchers, **ProclivityPy** aims at providing missing boundary conditions
in integrated district energy assessment simulations related to human behavior, such as the use of appliances and 
lighting, space heating settings and domestic hot water redrawals.

**ProclivityPy** is also highly customizable and extensible, accepting model changes or extensions defined by users. 
For more information on the implementation, see the [GitHub Wiki]
(https://github.com/rubenbaetens/ProclivityPy/wiki).

##Example

```python
family = Household("Example family")
family.parameterize()
family.simulate()
```
