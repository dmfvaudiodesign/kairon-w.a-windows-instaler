#define MyAppName "KAIRON WA"
#define MyAppVersion "0.1.0-dev"
#define MyAppPublisher "DMFV Audio Design"
#define PayloadDir "build\payload"

[Setup]
AppId={{7E2285C6-97D4-4F56-AE7B-4D2B28E9D815}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\KAIRON WA
DefaultGroupName=KAIRON WA
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableDirPage=yes
DisableReadyPage=yes
OutputDir=output
OutputBaseFilename=KAIRON-WA-Setup-Windows
SetupIconFile=payload\kairon-wa.ico
UninstallDisplayIcon={app}\kairon-wa.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=no
RestartApplications=no
WizardResizable=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: checkedonce
Name: "autostart"; Description: "Iniciar o KAIRON WA com o Windows"; GroupDescription: "Inicialização:"; Flags: checkedonce

[Dirs]
Name: "{app}\app\data"; Flags: uninsneveruninstall
Name: "{app}\app\data\logs"; Flags: uninsneveruninstall
Name: "{app}\app\data\media"; Flags: uninsneveruninstall
Name: "{app}\app\data\plugins"; Flags: uninsneveruninstall

[Files]
Source: "{#PayloadDir}\runtime\*"; DestDir: "{app}\runtime"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PayloadDir}\app\*"; DestDir: "{app}\app"; Excludes: "data\*,.env"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PayloadDir}\app\.env"; DestDir: "{app}\app"; DestName: ".env"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "payload\launcher.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "payload\stop.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "payload\show-access-key.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "payload\kairon-wa.ico"; DestDir: "{app}"; Flags: ignoreversion
; Telas compostas geradas por tools/render_ui.py (uma versão por escala de DPI)
Source: "assets\ui\*.bmp"; Flags: dontcopy

[Icons]
Name: "{group}\KAIRON WA"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\kairon-wa.ico"
Name: "{group}\Mostrar chave de acesso"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\show-access-key.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\kairon-wa.ico"
Name: "{group}\Desinstalar KAIRON WA"; Filename: "{uninstallexe}"
Name: "{autodesktop}\KAIRON WA"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\kairon-wa.ico"; Tasks: desktopicon
Name: "{userstartup}\KAIRON WA"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher.vbs"" --background"; WorkingDir: "{app}"; IconFilename: "{app}\kairon-wa.ico"; Tasks: autostart

[Run]
Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher.vbs"""; Description: "Abrir o KAIRON WA"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\wscript.exe"; Parameters: """{app}\stop.vbs"""; Flags: runhidden waituntilterminated skipifdoesntexist

[Code]
{ ---------------------------------------------------------------------------
  Interface personalizada do KAIRON WA

  POR QUE ESTE CÓDIGO É ASSIM:
  - TNewStaticText e TPanel são controles com janela própria e NÃO são
    transparentes: pintavam caixas pretas atrás dos textos, e com o tema do
    Windows o TPanel ignora a cor (botão "Avançar" e barra de progresso pretos).
  - BMP não tem transparência: o logo aparecia com o fundo magenta.

  SOLUÇÃO: cada tela é uma imagem já composta (tools/render_ui.py) exibida num
  TBitmapImage. Por cima ficam só controles SEM janela própria (TBitmapImage e
  TLabel transparente), que são desenhados direto sobre o fundo:
  - barra de progresso = recorte da própria tela com a barra cheia, revelado
    da esquerda para a direita;
  - marcadores das etapas = recortes "ativo"/"concluído"/"pendente";
  - áreas clicáveis = TLabel transparente sobre os botões desenhados.
  Os botões nativos continuam existindo (fora da área visível) para que
  Enter, Esc e o "X" da janela funcionem normalmente.

  As coordenadas abaixo são as MESMAS de tools/render_ui.py (base 960 x 640).
  --------------------------------------------------------------------------- }
const
  BaseWidth = 960;
  BaseHeight = 640;

  ProgX1 = 150; ProgY1 = 340; ProgX2 = 790; ProgY2 = 362;
  MarkY = 486; MarkHalf = 15;
  PercentX = 804; PercentY = 337; PercentW = 110; PercentH = 30;

  StateNone = -1; StatePending = 0; StateActive = 1; StateDone = 2;

var
  UiScale: Integer;
  Background: TBitmapImage;
  ProgressFill: TBitmapImage;
  StageMarks: array of TBitmapImage;
  StageStates: array of Integer;
  PercentLabel: TLabel;
  HotNext, HotCancel, HotFinish: TLabel;
  LastPercent: Integer;
  NativeBackLeft, NativeNextLeft, NativeCancelLeft: Integer;
  CustomScreen: Boolean;

{ Mesmo arredondamento de render_ui.py: S(v) = (v * P + 50) div 100 }
function S(V: Integer): Integer;
begin
  Result := (V * UiScale + 50) div 100;
end;

function UiFile(const Name: String): String;
begin
  Result := Name + '_' + IntToStr(UiScale) + '.bmp';
end;

function UiPath(const Name: String): String;
begin
  Result := ExpandConstant('{tmp}\') + UiFile(Name);
end;

procedure ExtractUi(const Name: String);
begin
  ExtractTemporaryFile(UiFile(Name));
end;

procedure PickUiScale;
var
  P: Integer;
begin
  { Escolhe o conjunto de imagens mais próximo da escala do Windows }
  P := ScaleX(100);
  if P < 113 then UiScale := 100
  else if P < 138 then UiScale := 125
  else if P < 175 then UiScale := 150
  else UiScale := 200;
end;

function StageMarkLeft(Index: Integer): Integer;
begin
  { centro do marcador = início da coluna + 42; colunas de 175 a partir de x=130 }
  Result := 130 + Index * 175 + 42 - MarkHalf;
end;

function NewHotArea(X1, Y1, X2, Y2: Integer): TLabel;
begin
  Result := TLabel.Create(WizardForm);
  Result.Parent := WizardForm;
  Result.AutoSize := False;
  Result.Transparent := True;
  Result.Caption := '';
  Result.SetBounds(S(X1), S(Y1), S(X2) - S(X1), S(Y2) - S(Y1));
  Result.Cursor := crHand;
  Result.Visible := False;
end;

procedure NativeNextClick(Sender: TObject);
begin
  if WizardForm.NextButton.Enabled then
    WizardForm.NextButton.OnClick(WizardForm.NextButton);
end;

procedure NativeCancelClick(Sender: TObject);
begin
  if WizardForm.CancelButton.Enabled then
    WizardForm.CancelButton.OnClick(WizardForm.CancelButton);
end;

{ Mostra/oculta a interface nativa (usada só em páginas inesperadas,
  por exemplo "Preparando para instalar" quando há arquivos em uso). }
procedure UseNativeUi(Native: Boolean);
begin
  WizardForm.OuterNotebook.Visible := Native;
  if Native then
  begin
    WizardForm.BackButton.Left := NativeBackLeft;
    WizardForm.NextButton.Left := NativeNextLeft;
    WizardForm.CancelButton.Left := NativeCancelLeft;
  end
  else
  begin
    { Fora da área visível, mas ainda "visíveis" para o Inno Setup:
      assim Enter/Esc e o botão X da janela continuam funcionando. }
    WizardForm.BackButton.Left := -S(4000);
    WizardForm.NextButton.Left := -S(4000);
    WizardForm.CancelButton.Left := -S(4000);
  end;
end;

procedure SetStageState(Index, State: Integer);
var
  Name: String;
begin
  if StageStates[Index] = State then Exit;
  StageStates[Index] := State;
  case State of
    StateActive: Name := 'active';
    StateDone: Name := 'done';
  else
    Name := 'pending';
  end;
  StageMarks[Index].Bitmap.LoadFromFile(UiPath('stage' + IntToStr(Index + 1) + '_' + Name));
end;

procedure UpdateInstallProgress(Percent: Integer);
var
  FullWidth, FillWidth, I, Active: Integer;
begin
  if Percent < 0 then Percent := 0;
  if Percent > 100 then Percent := 100;
  if Percent = LastPercent then Exit;
  LastPercent := Percent;

  FullWidth := S(ProgX2) - S(ProgX1);
  FillWidth := (FullWidth * Percent) div 100;
  if FillWidth < 1 then
    ProgressFill.Visible := False
  else
  begin
    ProgressFill.Width := FillWidth;
    ProgressFill.Visible := True;
  end;
  PercentLabel.Caption := IntToStr(Percent) + '%';

  { Etapas: 0-24 copiando, 25-54 configurando, 55-81 registrando, 82-99 finalizando }
  if Percent < 25 then Active := 0
  else if Percent < 55 then Active := 1
  else if Percent < 82 then Active := 2
  else if Percent < 100 then Active := 3
  else Active := 4;
  for I := 0 to 3 do
    if I < Active then SetStageState(I, StateDone)
    else if I = Active then SetStageState(I, StateActive)
    else SetStageState(I, StatePending);
end;

procedure HideOverlays;
var
  I: Integer;
begin
  ProgressFill.Visible := False;
  PercentLabel.Visible := False;
  for I := 0 to 3 do StageMarks[I].Visible := False;
  HotNext.Visible := False;
  HotCancel.Visible := False;
  HotFinish.Visible := False;
end;

procedure ShowWelcomeScreen;
begin
  Background.Bitmap.LoadFromFile(UiPath('welcome'));
  HotNext.SetBounds(S(770), S(566), S(932) - S(770), S(618) - S(566));
  HotCancel.SetBounds(S(590), S(566), S(752) - S(590), S(618) - S(566));
  HotNext.Visible := True;
  HotCancel.Visible := True;
end;

procedure ShowInstallingScreen;
var
  I: Integer;
begin
  Background.Bitmap.LoadFromFile(UiPath('installing'));
  for I := 0 to 3 do
  begin
    StageStates[I] := StateNone;
    StageMarks[I].Visible := True;
  end;
  LastPercent := -1;
  UpdateInstallProgress(0);
  PercentLabel.Visible := True;
  HotCancel.SetBounds(S(770), S(566), S(932) - S(770), S(618) - S(566));
  HotCancel.Visible := True;
end;

procedure ShowFinishedScreen;
begin
  Background.Bitmap.LoadFromFile(UiPath('finished'));
  HotFinish.Visible := True;
end;

procedure InitializeWizard;
var
  I: Integer;
begin
  PickUiScale;
  ExtractUi('welcome');
  ExtractUi('installing');
  ExtractUi('finished');
  ExtractUi('progress');
  for I := 1 to 4 do
  begin
    ExtractUi('stage' + IntToStr(I) + '_pending');
    ExtractUi('stage' + IntToStr(I) + '_active');
    ExtractUi('stage' + IntToStr(I) + '_done');
  end;

  WizardForm.Caption := 'Instalação - KAIRON WA';
  WizardForm.Color := clBlack;
  WizardForm.ClientWidth := S(BaseWidth);
  WizardForm.ClientHeight := S(BaseHeight);
  WizardForm.Position := poScreenCenter;
  WizardForm.Bevel.Visible := False;

  { Posições nativas (já ajustadas ao novo tamanho pelas âncoras) }
  NativeBackLeft := WizardForm.BackButton.Left;
  NativeNextLeft := WizardForm.NextButton.Left;
  NativeCancelLeft := WizardForm.CancelButton.Left;

  { 1) Fundo: a tela inteira já composta }
  Background := TBitmapImage.Create(WizardForm);
  Background.Parent := WizardForm;
  Background.SetBounds(0, 0, S(BaseWidth), S(BaseHeight));
  Background.Stretch := False;
  Background.Center := False;
  Background.BackColor := clBlack;

  { 2) Barra de progresso: recorte da barra cheia, revelado pela largura }
  ProgressFill := TBitmapImage.Create(WizardForm);
  ProgressFill.Parent := WizardForm;
  ProgressFill.Stretch := False;
  ProgressFill.Center := False;
  ProgressFill.AutoSize := False;
  ProgressFill.Bitmap.LoadFromFile(UiPath('progress'));
  ProgressFill.SetBounds(S(ProgX1), S(ProgY1), S(ProgX2) - S(ProgX1), S(ProgY2) - S(ProgY1));

  { 3) Marcadores das etapas }
  SetArrayLength(StageMarks, 4);
  SetArrayLength(StageStates, 4);
  for I := 0 to 3 do
  begin
    StageMarks[I] := TBitmapImage.Create(WizardForm);
    StageMarks[I].Parent := WizardForm;
    StageMarks[I].Stretch := False;
    StageMarks[I].Center := False;
    StageMarks[I].AutoSize := False;
    StageMarks[I].SetBounds(S(StageMarkLeft(I)), S(MarkY - MarkHalf),
      S(StageMarkLeft(I) + 2 * MarkHalf) - S(StageMarkLeft(I)),
      S(MarkY + MarkHalf) - S(MarkY - MarkHalf));
    StageStates[I] := StateNone;
  end;

  { 4) Porcentagem (TLabel transparente: sem caixa preta) }
  PercentLabel := TLabel.Create(WizardForm);
  PercentLabel.Parent := WizardForm;
  PercentLabel.AutoSize := False;
  PercentLabel.Transparent := True;
  PercentLabel.SetBounds(S(PercentX), S(PercentY), S(PercentW), S(PercentH));
  PercentLabel.Font.Name := 'Segoe UI';
  PercentLabel.Font.Height := -S(20);
  PercentLabel.Font.Style := [fsBold];
  PercentLabel.Font.Color := clWhite;
  PercentLabel.Caption := '0%';

  { 5) Áreas clicáveis sobre os botões desenhados }
  HotNext := NewHotArea(770, 566, 932, 618);
  HotNext.OnClick := @NativeNextClick;
  HotCancel := NewHotArea(590, 566, 752, 618);
  HotCancel.OnClick := @NativeCancelClick;
  HotFinish := NewHotArea(308, 470, 652, 530);
  HotFinish.OnClick := @NativeNextClick;

  HideOverlays;
  UseNativeUi(False);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  HideOverlays;
  CustomScreen := (CurPageID = wpWelcome) or (CurPageID = wpInstalling) or (CurPageID = wpFinished);
  UseNativeUi(not CustomScreen);
  Background.Visible := CustomScreen;
  if CurPageID = wpWelcome then ShowWelcomeScreen
  else if CurPageID = wpInstalling then ShowInstallingScreen
  else if CurPageID = wpFinished then ShowFinishedScreen;
end;

procedure CurInstallProgressChanged(CurProgress, MaxProgress: Integer);
begin
  if MaxProgress <= 0 then
    UpdateInstallProgress(0)
  else
    UpdateInstallProgress(Round(CurProgress * 100.0 / MaxProgress));
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (PageID = wpSelectTasks);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  StopScript: String;
begin
  if CurStep = ssInstall then
  begin
    StopScript := ExpandConstant('{app}\stop.vbs');
    if FileExists(StopScript) then
      Exec(ExpandConstant('{sys}\wscript.exe'), '"' + StopScript + '"', '', SW_HIDE,
        ewWaitUntilTerminated, ResultCode);
  end
  else if CurStep = ssPostInstall then
    UpdateInstallProgress(100);
end;
