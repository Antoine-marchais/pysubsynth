import matplotlib.pyplot as plt


def plot_waves(waves, labels=None):
    fig, ax = plt.subplots()
    ax.set_ylabel("amplitude")
    ax.set_xlabel("timestep")
    if labels is not None and len(waves) == len(labels):
        for label, wave in zip(labels, waves):
            ax.plot(wave, label=label)
        ax.legend()
    else:
        for wave in waves:
            ax.plot(wave)