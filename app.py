from ttkbootstrap.constants import *
import ttkbootstrap as ttk

from tkinter.filedialog import askopenfilename, asksaveasfile

from av.audio.fifo import AudioFifo
import av
import io


class MainWindow(ttk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry('245x200')
        self.resizable(FALSE, FALSE)

        self.media = None
        self.values = None

        container = ttk.Frame(self)
        container.pack(side=TOP, fill=X, pady=5)

        self.open_entry = ttk.Entry(container, width=30)
        self.open_entry.bind('<Return>', self.on_open)
        self.open_entry.grid(row=0, column=0)

        open_btn = ttk.Button(container, text='open', command=self.on_open)
        open_btn.grid(row=0, column=1)

        self.combobox = ttk.Combobox(container)
        self.combobox.grid(row=1, column=0, columnspan=2, sticky=W+E, pady=5)

        save_btn = ttk.Button(container, text='save', command=self.on_save)
        save_btn.grid(row=2, column=0, columnspan=2, sticky=W+E, pady=5)

    def on_open(self):
        file_path = askopenfilename()

        if len(self.open_entry.get()) == 0:
            self.open_entry.insert(0, file_path)

        if self.media is None:
            self.media = MediaHandler(file_path)
            self.values = self.media.get_input_streams()
            self.combobox.config(values=self.values)

    def on_save(self):
        stream = self.combobox.get()
        if self.media is not None:
            if self.values is not None:
                for value in self.values:
                    if str(value) == stream:
                        print('YES')
                        self.media.handle(value)


class MediaHandler:
    def __init__(self, path):
        self.input_container = av.open(path, 'r')
        self.path = path

    def get_input_streams(self):
        return self.input_container.streams.get()

    def handle(self, stream):
        self.input_container = av.open(self.path, 'r')
        input_file_info = self._get_stream_info(stream)

        if stream.type == 'audio':
            output_container = av.open('output.mp3', 'w')
            output_stream = output_container.add_stream(codec_name='mp3', rate=input_file_info['sample_rate'])

            for packet in self.input_container.demux(stream):
                if packet.dts is None:
                    continue
                else:
                    for frame in packet.decode():
                        output_container.mux(output_stream.encode(frame))

            self.input_container.close()
            output_container.close()

        elif stream.type == 'video':
            output_container = av.open('output.mp4', 'w')
            output_stream = output_container.add_stream(template=stream)

            for packet in self.input_container.demux(stream):
                if packet.dts is None:
                    continue
                else:
                    packet.stream = output_stream
                    output_container.mux(packet)

            self.input_container.close()
            output_container.close()

    @staticmethod
    def _get_stream_info(stream):
        cc = stream.codec_context
        stream_options = {
            'index': stream.index,
            'start_time': stream.start_time,
            'time_base': stream.time_base,
            'duration': stream.duration,
            'frame_count': stream.frames,
            'profile': stream.profile,
            'language': stream.language
        }

        if stream.type == 'video':
            video_stream_options = {
                'fps': stream.base_rate,
                'width': cc.width,
                'height': cc.height,
                'aspect_ratio': cc.sample_aspect_ratio
            }

            for k, v in video_stream_options.items():
                stream_options[k] = v

        if stream.type == 'audio':
            audio_stream_options = {
                'frame_size': cc.frame_size,
                'sample_rate': stream.sample_rate
            }

            for k, v in audio_stream_options.items():
                stream_options[k] = v

        return stream_options


if __name__ == '__main__':
    MainWindow(title='Media Get Mater', themename='superhero').mainloop()