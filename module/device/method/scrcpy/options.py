import typing as t

import module.device.method.scrcpy.const as const


class ScrcpyOptions:
    frame_rate = 6

    @classmethod
    def codec_options(cls) -> str:
        """
        Custom codec options passing through scrcpy.
        https://developer.android.com/reference/android/media/MediaFormat

        Returns:
            key_profile=1,key_level=4096,...
        """
        options = dict(
            # H.264 profile and level
            # https://developer.android.com/reference/android/media/MediaCodecInfo.CodecProfileLevel
            # Baseline, which only has I/P frames
            key_profile=1,
            # Level 4.1, for 1280x720@30fps
            key_level=4096,
            # Max quality
            key_quality=100,
            # https://developer.android.com/reference/android/media/MediaCodecInfo.EncoderCapabilities
            # Constant quality
            key_bitrate_mode=0,
            # A zero value means a stream containing all key frames is requested.
            key_i_frame_interval=0,
            # https://developer.android.com/reference/android/media/MediaCodecInfo.CodecCapabilities
            # COLOR_Format24bitBGR888
            key_color_format=12,
            # The same as output frame rate to lower CPU consumption
            key_capture_rate=cls.frame_rate,
            # 20Mbps, the maximum output bitrate of scrcpy
            key_bit_rate=20000000,
        )
        return ','.join([f'{k}={v}' for k, v in options.items()])

    @classmethod
    def arguments(cls) -> t.List[str]:
        """
        https://github.com/Genymobile/scrcpy/blob/master/server/src/main/java/com/genymobile/scrcpy/Server.java
        https://github.com/Genymobile/scrcpy/blob/master/server/src/main/java/com/genymobile/scrcpy/Options.java

        Returns:
            ['log_level=info', 'max_size=1280', ...]
        """
        options = [
            'log_level=info',
            'max_size=1280',
            # 20Mbps, the maximum output bitrate of scrcpy
            # If a higher value is set, scrcpy fallback to 8Mbps default.
            'bit_rate=20000000',
            # Screenshot time cost <= 300ms is enough for human speed.
            f'max_fps={cls.frame_rate}',
            # No orientation lock
            f'lock_video_orientation={const.LOCK_SCREEN_ORIENTATION_UNLOCKED}',
            # Always true
            'tunnel_forward=true',
            # Always true for controlling via scrcpy
            'control=true',
            # Default to 0
            'display_id=0',
            # Useless, always false
            'show_touches=false',
            # Not determined, leave it as default
            'stay_awake=false',
            # Encoder name
            # Should in [
            #     "OMX.google.h264.encoder",
            #     "OMX.qcom.video.encoder.avc",
            #     "c2.qti.avc.encoder",
            #     "c2.android.avc.encoder",
            # ]
            # Empty value, let scrcpy to decide
            # 'encoder_name=',
            # Codec options
            f'codec_options={cls.codec_options()}',
            # Useless, always false
            'power_off_on_close=false',
            'clipboard_autosync=false',
            'downsize_on_error=false',
        ]
        return options

    @classmethod
    def command_v125(cls, jar_path='/data/local/tmp/scrcpy-server.jar') -> t.List[str]:
        """
        Generate the commands to run scrcpy.
        """
        commands = [
            f'CLASSPATH={jar_path}',
            'app_process',
            '/',
            'com.genymobile.scrcpy.Server',
            '1.25',
        ]
        commands += cls.arguments()
        return commands

    @classmethod
    def command_v120(cls, jar_path='/data/local/tmp/scrcpy-server.jar') -> t.List[str]:
        commands = [
            f"CLASSPATH={jar_path}",
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            "1.20",  # Scrcpy server version
            "info",  # Log level: info, verbose...
            f"1280",  # Max screen width (long side)
            f"20000000",  # Bitrate of video
            f"{cls.frame_rate}",  # Max frame per second
            f"{const.LOCK_SCREEN_ORIENTATION_UNLOCKED}",  # Lock screen orientation: LOCK_SCREEN_ORIENTATION
            "true",  # Tunnel forward
            "-",  # Crop screen
            "false",  # Send frame rate to client
            "true",  # Control enabled
            "0",  # Display id
            "false",  # Show touches
            "false",  # Stay awake
            cls.codec_options(),  # Codec (video encoding) options
            "-",  # Encoder name
            "false",  # Power off screen after server closed
        ]
        return commands


if __name__ == '__main__':
    print(' '.join(ScrcpyOptions.command_v120()))
