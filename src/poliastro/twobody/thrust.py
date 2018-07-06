import numpy as np

from poliastro.twobody.decorators import state_from_vector
from poliastro.util import norm, circular_velocity


def edelbaum_ai(k, a_0, a_f, inc_0, inc_f, f):
    """Guidance law from the Edelbaum/Kéchichian theory, optimal transfer between circular inclined orbits
       (a_0, i_0) --> (a_f, i_f), ecc = 0.
    Parameters
    ----------
    k : float
        Gravitational parameter.
    a_0 : float
        Initial semimajor axis.
    a_f : float
        Final semimajor axis.
    inc_0 : float
        Initial inclination.
    inc_f : float
        Final inclination.
    f : float
        Magnitude of constant acceleration

    Notes
    -----
    Edelbaum theory, reformulated by Kéchichian.

    References
    ----------
    * Edelbaum, T. N. "Propulsion Requirements for Controllable
      Satellites", 1961.
    * Kéchichian, J. A. "Reformulation of Edelbaum's Low-Thrust
      Transfer Problem Using Optimal Control Theory", 1997.
    """

    def _beta_0(V_0, V_f, inc_0, inc_f):
        """Compute initial yaw angle (β) as a function of the problem parameters.
        """
        delta_i_f = abs(inc_f - inc_0)
        return np.arctan2(np.sin(np.pi / 2 * delta_i_f), V_0 / V_f - np.cos(np.pi / 2 * delta_i_f))

    def _compute_parameters(k, a_0, a_f, inc_0, inc_f):
        """Compute parameters of the model.
        """
        delta_inc = abs(inc_f - inc_0)
        V_0 = circular_velocity(k, a_0)
        V_f = circular_velocity(k, a_f)
        beta_0_ = _beta_0(V_0, V_f, inc_0, inc_f)

        return V_0, beta_0_, delta_inc

    def _beta(t, *, V_0, f, beta_0):
        """Compute yaw angle (β) as a function of time and the problem parameters.
        """
        return np.arctan2(V_0 * np.sin(beta_0), V_0 * np.cos(beta_0) - f * t)

    def _delta_V(V_0, beta_0, inc_0, inc_f):
        """Compute required increment of velocity.
        """
        delta_i_f = abs(inc_f - inc_0)
        return V_0 * np.cos(beta_0) - V_0 * np.sin(beta_0) / np.tan(np.pi / 2 * delta_i_f + beta_0)

    def _extra_quantities(k, a_0, a_f, inc_0, inc_f, f):
        """Extra quantities given by the Edelbaum (a, i) model.
        """
        V_0, beta_0_, _ = _compute_parameters(k, a_0, a_f, inc_0, inc_f)
        delta_V_ = _delta_V(V_0, beta_0_, inc_0, inc_f)
        t_f_ = delta_V_ / f

        return delta_V_, t_f_

    V_0, beta_0_, _ = _compute_parameters(k, a_0, a_f, inc_0, inc_f)

    @state_from_vector
    def a_d(t0, ss):
        r = ss.r.value
        v = ss.v.value

        # Change sign of beta with the out-of-plane velocity
        beta_ = _beta(t0, V_0=V_0, f=f, beta_0=beta_0_) * np.sign(r[0] * (inc_f - inc_0))

        t_ = v / norm(v)
        w_ = np.cross(r, v) / norm(np.cross(r, v))
        # n_ = np.cross(t_, w_)
        accel_v = f * (
            np.cos(beta_) * t_ +
            np.sin(beta_) * w_
        )
        return accel_v

    delta_V, t_f = _extra_quantities(k, a_0, a_f, inc_0, inc_f, f)
    return a_d, delta_V, t_f
