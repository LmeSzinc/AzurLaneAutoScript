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
        options = {
            # H.264 profile and level
            # https://developer.android.com/reference/android/media/MediaCodecInfo.CodecProfileLevel
            # Baseline, which only has I/P frames
            "key_profile": 1,
            # Level 4.1, for 1280x720@30fps
            "key_level": 4096,
            # Max quality
            "key_quality": 100,
            # https://developer.android.com/reference/android/media/MediaCodecInfo.EncoderCapabilities
            # Constant quality
            "key_bitrate_mode": 0,
            # A zero value means a stream containing all key frames is requested.
            "key_i_frame_interval": 0,
            # https://developer.android.com/reference/android/media/MediaCodecInfo.CodecCapabilities
            # COLOR_Format24bitBGR888
            "key_color_format": 12,
            # The same as output frame rate to lower CPU consumption
            "key_capture_rate": cls.frame_rate,
            # 20Mbps, the maximum output bitrate of scrcpy
            "key_bit_rate": 20000000,
        }
        return ",".join([f"{k}={v}" for k, v in options.items()])


    @classmethod
    def command_v120(cls, jar_path="/data/local/tmp/scrcpy-server.jar") -> list[str]:
        commands = [
            f"CLASSPATH={jar_path}",
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            "1.20",  # Scrcpy server version
            "info",  # Log level: info, verbose...
            "1280",  # Max screen width (long side)
            "20000000",  # Bitrate of video
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


if __name__ == "__main__":
    print(" ".join(ScrcpyOptions.command_v120()))
