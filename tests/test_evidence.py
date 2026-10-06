import numpy as np
from gems48.evidence import discounted_binary_mass, combine_yager, minmax_unit

def test_yager_mass_conservation_and_conflict():
    a=discounted_binary_mass(np.array([[1.,0.]]),.9)
    b=discounted_binary_mass(np.array([[0.,1.]]),.8)
    f,n,u,k=combine_yager(a,b)
    assert np.allclose(f+n+u,1)
    assert np.all(k>0)
    assert np.all(u>=k)

def test_agreement_has_no_conflict():
    x=np.array([[0.,1.]])
    *_,k=combine_yager(discounted_binary_mass(x,.9),discounted_binary_mass(x,.8))
    assert np.array_equal(k,np.zeros_like(k))

def test_normalization_range():
    out=minmax_unit(np.array([[2.,4.],[3.,99.]]),np.array([[1,1],[1,0]],bool))
    assert out.min()==0 and out.max()==1 and out[1,1]==0

def test_rejects_invalid_confidence_and_reliability():
    import pytest
    with pytest.raises(ValueError): discounted_binary_mass(np.array([1.1]), .8)
    with pytest.raises(ValueError): discounted_binary_mass(np.array([.5]), 1.1)
