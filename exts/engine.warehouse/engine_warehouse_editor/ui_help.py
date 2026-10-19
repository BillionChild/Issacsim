"""Readable local UI styles and Korean hover help; no simulation behavior."""
import omni.ui as ui

STYLE={
    'Label':{'font_size':18},
    'Button.Label':{'font_size':18},
    'ComboBox':{'font_size':18},
    'CollapsableFrame':{'font_size':18},
}
HELP={
    'Load three-engine demo':'엔진 3개의 입고·수리 복귀·출고 시나리오를 불러옵니다.\n장면 교체 전 저장 안내를 확인하세요. 불러온 뒤 케이스를 선택하고 Play를 누릅니다.',
    'Apply case':'선택한 이상 상황을 첫 번째 엔진에 적용합니다.\n진행 중에는 바꿀 수 없습니다. Reset → 케이스 선택 → Apply case 순서로 사용하세요.',
    'Play':'컨베이어와 로봇 시연을 시작하거나 일시정지한 시연을 이어갑니다.\n첫 엔진은 카메라 영상으로 자세를 추정한 뒤 보정 집기를 수행합니다.',
    'Pause':'현재 자세와 진행 상태를 유지한 채 일시정지합니다.\n카메라 화면이나 보정 결과를 설명할 때 사용하세요.',
    'Reset':'전체 시나리오를 처음으로 되돌립니다.\n선택한 이상 케이스는 유지하지만 측정 결과·기록·재촬영 횟수는 초기화됩니다.',
    'Monitor':'문제 발견·보정·안착 검증과 창고 재고를 보여주는 현황판을 엽니다.',
    'Robot camera':'로봇에 부착된 가상 카메라의 실시간 시점을 엽니다.\n가림 테스트용 마스크는 추론 이미지에 적용되며 이 실시간 화면에는 나타나지 않습니다.',
    'Overview':'메인 화면을 공정 전체를 볼 수 있는 원근 시점으로 전환합니다.',
    'Retry observation':'HOLD 상태에서 같은 위치를 다시 촬영하고 판단합니다.\n가림을 제거하지 않으므로 가림이 남아 있으면 계속 HOLD합니다.',
    'Clear camera mask + retry':'사용자가 가상 카메라 가림을 해제한 뒤 다시 촬영합니다.\n새 영상이 승인돼야 로봇이 재개합니다. 로봇이 장애물을 직접 치우는 동작은 아닙니다.',
    'Load single-engine project':'개발용 단일 엔진 시나리오를 불러옵니다.\n포트폴리오 연속 시연에는 Load three-engine demo를 사용하세요.',
    'Open pickup anomaly lab':'이상 상황 주입·영상 추정·집기 보정을 개별 시험하는 개발용 실험실을 엽니다.',
    'Export timing / performance CSV':'현재 시뮬레이션 이벤트·성능·검증 결과를 outputs 폴더에 저장합니다.\nReset 전에 내보내세요. 같은 이름의 이전 결과는 덮어씁니다.',
    'Request outbound':'단일 엔진 모드의 출고를 요청합니다.\n3엔진 모드는 Monitor의 수동 출고 기능을 사용하세요.',
    'Repair complete -> Reinspect':'단일 엔진 수리 대기 상태에서 보완 작업 완료를 알리고 재검사를 시작합니다.',
    'Reload Code + Reset':'수정한 동작 코드를 다시 읽고 시나리오를 초기화합니다.\nUI 코드 변경은 확장을 OFF → ON 해야 반영됩니다.',
    'Rebuild + Check Motion':'개발용 로봇 경로 생성·검증을 실행합니다.\n일반 시연에는 필요하지 않으며 생성 시간이 걸릴 수 있습니다.',
    'Top camera':'메인 화면을 위에서 내려다보는 시점으로 바꿉니다.',
    'Auto demo':'Reset 직후 선택합니다. 정해진 순서대로 입고·출고를 자동 진행합니다.',
    'Manual outbound':'Reset 직후 선택합니다. 자동 출고 주문 대신 사용자가 출고할 엔진을 지정합니다.',
    'Request selected engine outbound':'선택한 재고 엔진의 출고 주문을 추가합니다.\n로봇과 출고 구간이 사용 가능해지면 처리하며, 불가능한 상태에서는 비활성화됩니다.',
}
CASE_HELP='첫 엔진에 넣을 이상 상황을 선택합니다.\nnormal: 정상 / stop_x: X 정지 오차 30mm\nlateral_y: Y 치우침 15mm / yaw: 회전 오차 2도\noccluded: 카메라 영상 가림\nx_y, x_yaw, y_yaw, x_y_yaw: 복합 위치·회전 오차\ncombined_occluded: 복합 오차 + 영상 가림\n선택 후 Apply case를 누르세요.'

def tooltip(text):
    def build():
        with ui.VStack(width=460,spacing=8,style={'background_color':0xff292522}):
            ui.Label(text,width=460,height=0,word_wrap=True,
                     style={'font':'C:/Windows/Fonts/malgun.ttf','font_size':18,'color':0xfff4f4f4,'margin':12})
    return build

def button(text,**kwargs):
    help_text=kwargs.pop('help_text',HELP.get(text))
    if not help_text and text in ('1x','2x','4x'):
        help_text=f'시연 재생 속도를 {text}로 변경합니다.\n시뮬레이션 기준 사이클타임 값은 바뀌지 않습니다.'
    if help_text:kwargs['tooltip_fn']=tooltip(help_text)
    return ui.Button(text,**kwargs)
