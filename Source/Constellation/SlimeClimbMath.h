#pragma once

// Lower scores are better. Extend the original reciprocal continuously below
// zero without its pole at -100 or the negative weights beyond that pole.
inline float SlimeClimbCandidateWeight(float Score)
{
    return Score < 0.f ? 1.f - Score * 0.01f : 1.f / (1.f + Score * 0.01f);
}
