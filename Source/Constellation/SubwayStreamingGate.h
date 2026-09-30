#pragma once
inline bool SubwayCanRetryLoad(bool Failed, bool Unloaded, double Elapsed, int RetryCount)
{
    return Failed && Unloaded && Elapsed >= 70 && RetryCount < 1;
}
struct FSubwayStreamingGate
{
    bool Update(float Forward, bool Inside, bool Ready, bool Busy)
    {
        if (Forward < -20)
            bArmed = true;
        return bArmed && Inside && Forward >= 0 && Ready && !Busy;
    }
    void Commit()
    {
        bArmed = false;
    }

  private:
    bool bArmed = true;
};
