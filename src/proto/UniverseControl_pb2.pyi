from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Universe(_message.Message):
    __slots__ = ["ftdi_dongle", "id", "physical_location", "remote_location"]
    class ArtNet(_message.Message):
        __slots__ = ["ip_address", "port", "universe_on_device"]
        IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
        PORT_FIELD_NUMBER: _ClassVar[int]
        UNIVERSE_ON_DEVICE_FIELD_NUMBER: _ClassVar[int]
        ip_address: str
        port: int
        universe_on_device: int
        def __init__(self, ip_address: _Optional[str] = ..., port: _Optional[int] = ..., universe_on_device: _Optional[int] = ...) -> None: ...
    class USBConfig(_message.Message):
        __slots__ = ["device_name", "product_id", "serial", "vendor_id"]
        DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
        PRODUCT_ID_FIELD_NUMBER: _ClassVar[int]
        SERIAL_FIELD_NUMBER: _ClassVar[int]
        VENDOR_ID_FIELD_NUMBER: _ClassVar[int]
        device_name: str
        product_id: int
        serial: str
        vendor_id: int
        def __init__(self, product_id: _Optional[int] = ..., vendor_id: _Optional[int] = ..., device_name: _Optional[str] = ..., serial: _Optional[str] = ...) -> None: ...
    FTDI_DONGLE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    PHYSICAL_LOCATION_FIELD_NUMBER: _ClassVar[int]
    REMOTE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    ftdi_dongle: Universe.USBConfig
    id: int
    physical_location: int
    remote_location: Universe.ArtNet
    def __init__(self, id: _Optional[int] = ..., physical_location: _Optional[int] = ..., remote_location: _Optional[_Union[Universe.ArtNet, _Mapping]] = ..., ftdi_dongle: _Optional[_Union[Universe.USBConfig, _Mapping]] = ...) -> None: ...

class artnet_device_enumeration_reply(_message.Message):
    __slots__ = ["artnet_devices", "integrated_dmx_ports", "integrated_midi_ports", "last_update_timestamp", "usb_devices"]
    class DiscoveredArtnetDevice(_message.Message):
        __slots__ = ["assigned_network_sub_switch_id", "assigned_network_switch_id", "background_discovery_can_be_controlled_by_artnet", "background_queue_policy", "background_queue_policy_raw", "background_queue_supported", "booted_from_secondary_source", "configuration_authority", "configured_sacn_priority", "device_firmware_revision", "device_hostname_or_ip", "device_ip_configured_by_dhcp", "device_is_squawking", "device_maximum_refresh_rate_in_hz", "device_port", "device_port_count", "device_port_direction_can_be_reconfigured", "device_position_in_bound_hirachy", "device_status_report", "device_style_code", "device_supports_15bit_port_addresses", "device_supports_dhcp", "device_supports_llrp", "device_supports_programmable_failsafe", "device_supports_rdm_setup_over_artnet", "device_supports_rdmnet", "device_supports_remote_output_configuration_using_artnet", "device_supports_switching_between_artnet_and_sacn", "device_supports_webbrowser_configuration", "device_user_data", "esta_manufacturer_id", "failsafe_state", "ip_of_bound_root_device", "mac_address", "macro_active", "oem_profuct_code", "operation_mode", "port_capabilities_and_status", "port_programming_identifier", "rdm_supported", "rdmnet_llrp_default_responder_uid", "switch_inputs_active", "ueba_bios_configured", "ueba_bios_version"]
        class BackgroundQueuePolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        class DeviceStyle(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        class FailsafeState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        class OperationMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        class PortProgrammingAuthority(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        class PortCapabilities(_message.Message):
            __slots__ = ["input_channel_includes_sip_packages", "input_channel_includes_test_packages", "input_channel_includes_text_packages", "input_channel_received_data", "input_converts_to_sacn", "input_is_disabled", "input_receive_errors_detected", "input_switch", "output_background_discovery_currently_running", "output_background_discovery_enabled", "output_channel_includes_sip_packages", "output_channel_includes_test_packages", "output_channel_includes_text_packages", "output_channel_transmitting_data", "output_converts_to_sacn", "output_dmx_wiring_short_detected", "output_is_merging_artnet_data", "output_merge_mode_is_ltp", "output_rdm_enabled", "output_style_is_delta", "output_switch", "port_can_publish_data_to_network", "port_can_receive_data_from_network", "port_type"]
            class PortType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                __slots__ = []
            ADB: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities.PortType
            ART_NET: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities.PortType
            AVAB: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities.PortType
            CMX: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities.PortType
            DALI: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities.PortType
            DMX: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities.PortType
            INPUT_CHANNEL_INCLUDES_SIP_PACKAGES_FIELD_NUMBER: _ClassVar[int]
            INPUT_CHANNEL_INCLUDES_TEST_PACKAGES_FIELD_NUMBER: _ClassVar[int]
            INPUT_CHANNEL_INCLUDES_TEXT_PACKAGES_FIELD_NUMBER: _ClassVar[int]
            INPUT_CHANNEL_RECEIVED_DATA_FIELD_NUMBER: _ClassVar[int]
            INPUT_CONVERTS_TO_SACN_FIELD_NUMBER: _ClassVar[int]
            INPUT_IS_DISABLED_FIELD_NUMBER: _ClassVar[int]
            INPUT_RECEIVE_ERRORS_DETECTED_FIELD_NUMBER: _ClassVar[int]
            INPUT_SWITCH_FIELD_NUMBER: _ClassVar[int]
            MIDI: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities.PortType
            OUTPUT_BACKGROUND_DISCOVERY_CURRENTLY_RUNNING_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_BACKGROUND_DISCOVERY_ENABLED_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_CHANNEL_INCLUDES_SIP_PACKAGES_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_CHANNEL_INCLUDES_TEST_PACKAGES_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_CHANNEL_INCLUDES_TEXT_PACKAGES_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_CHANNEL_TRANSMITTING_DATA_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_CONVERTS_TO_SACN_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_DMX_WIRING_SHORT_DETECTED_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_IS_MERGING_ARTNET_DATA_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_MERGE_MODE_IS_LTP_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_RDM_ENABLED_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_STYLE_IS_DELTA_FIELD_NUMBER: _ClassVar[int]
            OUTPUT_SWITCH_FIELD_NUMBER: _ClassVar[int]
            PORT_CAN_PUBLISH_DATA_TO_NETWORK_FIELD_NUMBER: _ClassVar[int]
            PORT_CAN_RECEIVE_DATA_FROM_NETWORK_FIELD_NUMBER: _ClassVar[int]
            PORT_TYPE_FIELD_NUMBER: _ClassVar[int]
            input_channel_includes_sip_packages: bool
            input_channel_includes_test_packages: bool
            input_channel_includes_text_packages: bool
            input_channel_received_data: bool
            input_converts_to_sacn: bool
            input_is_disabled: bool
            input_receive_errors_detected: bool
            input_switch: int
            output_background_discovery_currently_running: bool
            output_background_discovery_enabled: bool
            output_channel_includes_sip_packages: bool
            output_channel_includes_test_packages: bool
            output_channel_includes_text_packages: bool
            output_channel_transmitting_data: bool
            output_converts_to_sacn: bool
            output_dmx_wiring_short_detected: bool
            output_is_merging_artnet_data: bool
            output_merge_mode_is_ltp: bool
            output_rdm_enabled: bool
            output_style_is_delta: bool
            output_switch: int
            port_can_publish_data_to_network: bool
            port_can_receive_data_from_network: bool
            port_type: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities.PortType
            def __init__(self, port_can_receive_data_from_network: bool = ..., port_can_publish_data_to_network: bool = ..., port_type: _Optional[_Union[artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities.PortType, str]] = ..., input_converts_to_sacn: bool = ..., input_receive_errors_detected: bool = ..., input_is_disabled: bool = ..., input_channel_includes_text_packages: bool = ..., input_channel_includes_sip_packages: bool = ..., input_channel_includes_test_packages: bool = ..., input_channel_received_data: bool = ..., output_converts_to_sacn: bool = ..., output_merge_mode_is_ltp: bool = ..., output_dmx_wiring_short_detected: bool = ..., output_is_merging_artnet_data: bool = ..., output_channel_includes_text_packages: bool = ..., output_channel_includes_sip_packages: bool = ..., output_channel_includes_test_packages: bool = ..., output_channel_transmitting_data: bool = ..., input_switch: _Optional[int] = ..., output_switch: _Optional[int] = ..., output_background_discovery_enabled: bool = ..., output_background_discovery_currently_running: bool = ..., output_style_is_delta: bool = ..., output_rdm_enabled: bool = ...) -> None: ...
        ALL_OUTPUT_FULL: artnet_device_enumeration_reply.DiscoveredArtnetDevice.FailsafeState
        ALL_OUTPUT_ZERO: artnet_device_enumeration_reply.DiscoveredArtnetDevice.FailsafeState
        ARTNET_DMX_CONVERTER_NODE: artnet_device_enumeration_reply.DiscoveredArtnetDevice.DeviceStyle
        ASSIGNED_NETWORK_SUB_SWITCH_ID_FIELD_NUMBER: _ClassVar[int]
        ASSIGNED_NETWORK_SWITCH_ID_FIELD_NUMBER: _ClassVar[int]
        BACKGROUND_DISCOVERY_CAN_BE_CONTROLLED_BY_ARTNET_FIELD_NUMBER: _ClassVar[int]
        BACKGROUND_QUEUE_POLICY_FIELD_NUMBER: _ClassVar[int]
        BACKGROUND_QUEUE_POLICY_RAW_FIELD_NUMBER: _ClassVar[int]
        BACKGROUND_QUEUE_SUPPORTED_FIELD_NUMBER: _ClassVar[int]
        BACKUP_DEVICE: artnet_device_enumeration_reply.DiscoveredArtnetDevice.DeviceStyle
        BOOTED_FROM_SECONDARY_SOURCE_FIELD_NUMBER: _ClassVar[int]
        CONFIGURATION_AUTHORITY_FIELD_NUMBER: _ClassVar[int]
        CONFIGURED_SACN_PRIORITY_FIELD_NUMBER: _ClassVar[int]
        DEVICE_FIRMWARE_REVISION_FIELD_NUMBER: _ClassVar[int]
        DEVICE_HOSTNAME_OR_IP_FIELD_NUMBER: _ClassVar[int]
        DEVICE_IP_CONFIGURED_BY_DHCP_FIELD_NUMBER: _ClassVar[int]
        DEVICE_IS_SQUAWKING_FIELD_NUMBER: _ClassVar[int]
        DEVICE_MAXIMUM_REFRESH_RATE_IN_HZ_FIELD_NUMBER: _ClassVar[int]
        DEVICE_PORT_COUNT_FIELD_NUMBER: _ClassVar[int]
        DEVICE_PORT_DIRECTION_CAN_BE_RECONFIGURED_FIELD_NUMBER: _ClassVar[int]
        DEVICE_PORT_FIELD_NUMBER: _ClassVar[int]
        DEVICE_POSITION_IN_BOUND_HIRACHY_FIELD_NUMBER: _ClassVar[int]
        DEVICE_STATUS_REPORT_FIELD_NUMBER: _ClassVar[int]
        DEVICE_STYLE_CODE_FIELD_NUMBER: _ClassVar[int]
        DEVICE_SUPPORTS_15BIT_PORT_ADDRESSES_FIELD_NUMBER: _ClassVar[int]
        DEVICE_SUPPORTS_DHCP_FIELD_NUMBER: _ClassVar[int]
        DEVICE_SUPPORTS_LLRP_FIELD_NUMBER: _ClassVar[int]
        DEVICE_SUPPORTS_PROGRAMMABLE_FAILSAFE_FIELD_NUMBER: _ClassVar[int]
        DEVICE_SUPPORTS_RDMNET_FIELD_NUMBER: _ClassVar[int]
        DEVICE_SUPPORTS_RDM_SETUP_OVER_ARTNET_FIELD_NUMBER: _ClassVar[int]
        DEVICE_SUPPORTS_REMOTE_OUTPUT_CONFIGURATION_USING_ARTNET_FIELD_NUMBER: _ClassVar[int]
        DEVICE_SUPPORTS_SWITCHING_BETWEEN_ARTNET_AND_SACN_FIELD_NUMBER: _ClassVar[int]
        DEVICE_SUPPORTS_WEBBROWSER_CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
        DEVICE_USER_DATA_FIELD_NUMBER: _ClassVar[int]
        DIAGNOSTIC_TOOL: artnet_device_enumeration_reply.DiscoveredArtnetDevice.DeviceStyle
        DOES_NOT_APPLY: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortProgrammingAuthority
        ESTA_MANUFACTURER_ID_FIELD_NUMBER: _ClassVar[int]
        FAILSAFE_STATE_FIELD_NUMBER: _ClassVar[int]
        FRONT_PANEL_CONFIGURES_PORTS: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortProgrammingAuthority
        HOLD_LAST_STATE: artnet_device_enumeration_reply.DiscoveredArtnetDevice.FailsafeState
        IP_OF_BOUND_ROOT_DEVICE_FIELD_NUMBER: _ClassVar[int]
        LIGHTING_CONSOLE: artnet_device_enumeration_reply.DiscoveredArtnetDevice.DeviceStyle
        MACRO_ACTIVE_FIELD_NUMBER: _ClassVar[int]
        MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
        MEDIA_SERVER: artnet_device_enumeration_reply.DiscoveredArtnetDevice.DeviceStyle
        NETWORK_CONFIGURES_PORTS: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortProgrammingAuthority
        NETWORK_ROUTER: artnet_device_enumeration_reply.DiscoveredArtnetDevice.DeviceStyle
        OEM_PROFUCT_CODE_FIELD_NUMBER: _ClassVar[int]
        OPERATION_MODE_FIELD_NUMBER: _ClassVar[int]
        PLAYBACK_FAILSAFE_SCENE: artnet_device_enumeration_reply.DiscoveredArtnetDevice.FailsafeState
        PORT_CAPABILITIES_AND_STATUS_FIELD_NUMBER: _ClassVar[int]
        PORT_PROGRAMMING_IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
        PROGRAMMING_AUTHORITY_UNKNOWN: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortProgrammingAuthority
        RDMNET_LLRP_DEFAULT_RESPONDER_UID_FIELD_NUMBER: _ClassVar[int]
        RDM_SUPPORTED_FIELD_NUMBER: _ClassVar[int]
        STATE_LOCATE_IDENTIFY: artnet_device_enumeration_reply.DiscoveredArtnetDevice.OperationMode
        STATE_MUTE_BLACK: artnet_device_enumeration_reply.DiscoveredArtnetDevice.OperationMode
        STATE_NORMAL_OPERATION: artnet_device_enumeration_reply.DiscoveredArtnetDevice.OperationMode
        STATE_UNKNOWN: artnet_device_enumeration_reply.DiscoveredArtnetDevice.OperationMode
        STATUS_ADVISORY: artnet_device_enumeration_reply.DiscoveredArtnetDevice.BackgroundQueuePolicy
        STATUS_DISABLED: artnet_device_enumeration_reply.DiscoveredArtnetDevice.BackgroundQueuePolicy
        STATUS_ERROR: artnet_device_enumeration_reply.DiscoveredArtnetDevice.BackgroundQueuePolicy
        STATUS_MANUFACTURER_INFO: artnet_device_enumeration_reply.DiscoveredArtnetDevice.BackgroundQueuePolicy
        STATUS_NONE: artnet_device_enumeration_reply.DiscoveredArtnetDevice.BackgroundQueuePolicy
        STATUS_WARNING: artnet_device_enumeration_reply.DiscoveredArtnetDevice.BackgroundQueuePolicy
        SWITCH_INPUTS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
        UEBA_BIOS_CONFIGURED_FIELD_NUMBER: _ClassVar[int]
        UEBA_BIOS_VERSION_FIELD_NUMBER: _ClassVar[int]
        VISUALIZER: artnet_device_enumeration_reply.DiscoveredArtnetDevice.DeviceStyle
        assigned_network_sub_switch_id: int
        assigned_network_switch_id: int
        background_discovery_can_be_controlled_by_artnet: bool
        background_queue_policy: artnet_device_enumeration_reply.DiscoveredArtnetDevice.BackgroundQueuePolicy
        background_queue_policy_raw: int
        background_queue_supported: bool
        booted_from_secondary_source: bool
        configuration_authority: artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortProgrammingAuthority
        configured_sacn_priority: int
        device_firmware_revision: int
        device_hostname_or_ip: str
        device_ip_configured_by_dhcp: bool
        device_is_squawking: bool
        device_maximum_refresh_rate_in_hz: int
        device_port: int
        device_port_count: int
        device_port_direction_can_be_reconfigured: bool
        device_position_in_bound_hirachy: int
        device_status_report: str
        device_style_code: artnet_device_enumeration_reply.DiscoveredArtnetDevice.DeviceStyle
        device_supports_15bit_port_addresses: bool
        device_supports_dhcp: bool
        device_supports_llrp: bool
        device_supports_programmable_failsafe: bool
        device_supports_rdm_setup_over_artnet: bool
        device_supports_rdmnet: bool
        device_supports_remote_output_configuration_using_artnet: bool
        device_supports_switching_between_artnet_and_sacn: bool
        device_supports_webbrowser_configuration: bool
        device_user_data: int
        esta_manufacturer_id: int
        failsafe_state: artnet_device_enumeration_reply.DiscoveredArtnetDevice.FailsafeState
        ip_of_bound_root_device: str
        mac_address: str
        macro_active: _containers.RepeatedScalarFieldContainer[bool]
        oem_profuct_code: int
        operation_mode: artnet_device_enumeration_reply.DiscoveredArtnetDevice.OperationMode
        port_capabilities_and_status: _containers.RepeatedCompositeFieldContainer[artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities]
        port_programming_identifier: str
        rdm_supported: bool
        rdmnet_llrp_default_responder_uid: str
        switch_inputs_active: _containers.RepeatedScalarFieldContainer[bool]
        ueba_bios_configured: bool
        ueba_bios_version: int
        def __init__(self, device_hostname_or_ip: _Optional[str] = ..., device_port: _Optional[int] = ..., device_firmware_revision: _Optional[int] = ..., assigned_network_switch_id: _Optional[int] = ..., assigned_network_sub_switch_id: _Optional[int] = ..., oem_profuct_code: _Optional[int] = ..., ueba_bios_version: _Optional[int] = ..., operation_mode: _Optional[_Union[artnet_device_enumeration_reply.DiscoveredArtnetDevice.OperationMode, str]] = ..., configuration_authority: _Optional[_Union[artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortProgrammingAuthority, str]] = ..., booted_from_secondary_source: bool = ..., rdm_supported: bool = ..., ueba_bios_configured: bool = ..., esta_manufacturer_id: _Optional[int] = ..., port_programming_identifier: _Optional[str] = ..., device_status_report: _Optional[str] = ..., device_port_count: _Optional[int] = ..., port_capabilities_and_status: _Optional[_Iterable[_Union[artnet_device_enumeration_reply.DiscoveredArtnetDevice.PortCapabilities, _Mapping]]] = ..., configured_sacn_priority: _Optional[int] = ..., macro_active: _Optional[_Iterable[bool]] = ..., switch_inputs_active: _Optional[_Iterable[bool]] = ..., device_style_code: _Optional[_Union[artnet_device_enumeration_reply.DiscoveredArtnetDevice.DeviceStyle, str]] = ..., mac_address: _Optional[str] = ..., ip_of_bound_root_device: _Optional[str] = ..., device_position_in_bound_hirachy: _Optional[int] = ..., device_supports_webbrowser_configuration: bool = ..., device_ip_configured_by_dhcp: bool = ..., device_supports_dhcp: bool = ..., device_supports_15bit_port_addresses: bool = ..., device_supports_switching_between_artnet_and_sacn: bool = ..., device_is_squawking: bool = ..., device_supports_remote_output_configuration_using_artnet: bool = ..., device_supports_rdm_setup_over_artnet: bool = ..., background_discovery_can_be_controlled_by_artnet: bool = ..., background_queue_supported: bool = ..., device_supports_rdmnet: bool = ..., device_port_direction_can_be_reconfigured: bool = ..., device_supports_llrp: bool = ..., device_supports_programmable_failsafe: bool = ..., failsafe_state: _Optional[_Union[artnet_device_enumeration_reply.DiscoveredArtnetDevice.FailsafeState, str]] = ..., rdmnet_llrp_default_responder_uid: _Optional[str] = ..., device_user_data: _Optional[int] = ..., device_maximum_refresh_rate_in_hz: _Optional[int] = ..., background_queue_policy: _Optional[_Union[artnet_device_enumeration_reply.DiscoveredArtnetDevice.BackgroundQueuePolicy, str]] = ..., background_queue_policy_raw: _Optional[int] = ...) -> None: ...
    class USBDevice(_message.Message):
        __slots__ = ["manufacturer_id", "product_id"]
        MANUFACTURER_ID_FIELD_NUMBER: _ClassVar[int]
        PRODUCT_ID_FIELD_NUMBER: _ClassVar[int]
        manufacturer_id: int
        product_id: int
        def __init__(self, manufacturer_id: _Optional[int] = ..., product_id: _Optional[int] = ...) -> None: ...
    ARTNET_DEVICES_FIELD_NUMBER: _ClassVar[int]
    INTEGRATED_DMX_PORTS_FIELD_NUMBER: _ClassVar[int]
    INTEGRATED_MIDI_PORTS_FIELD_NUMBER: _ClassVar[int]
    LAST_UPDATE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    USB_DEVICES_FIELD_NUMBER: _ClassVar[int]
    artnet_devices: _containers.RepeatedCompositeFieldContainer[artnet_device_enumeration_reply.DiscoveredArtnetDevice]
    integrated_dmx_ports: int
    integrated_midi_ports: int
    last_update_timestamp: int
    usb_devices: _containers.RepeatedCompositeFieldContainer[artnet_device_enumeration_reply.USBDevice]
    def __init__(self, last_update_timestamp: _Optional[int] = ..., artnet_devices: _Optional[_Iterable[_Union[artnet_device_enumeration_reply.DiscoveredArtnetDevice, _Mapping]]] = ..., usb_devices: _Optional[_Iterable[_Union[artnet_device_enumeration_reply.USBDevice, _Mapping]]] = ..., integrated_dmx_ports: _Optional[int] = ..., integrated_midi_ports: _Optional[int] = ...) -> None: ...

class delete_universe(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class request_universe_list(_message.Message):
    __slots__ = ["universe_id"]
    UNIVERSE_ID_FIELD_NUMBER: _ClassVar[int]
    universe_id: int
    def __init__(self, universe_id: _Optional[int] = ...) -> None: ...

class universes_list(_message.Message):
    __slots__ = ["list_of_universes"]
    LIST_OF_UNIVERSES_FIELD_NUMBER: _ClassVar[int]
    list_of_universes: _containers.RepeatedCompositeFieldContainer[Universe]
    def __init__(self, list_of_universes: _Optional[_Iterable[_Union[Universe, _Mapping]]] = ...) -> None: ...
