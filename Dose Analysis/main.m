% % Wilson Oswald - Plot creation for CT Final project
% 
% 

clearvars;
close all;

%% 

data_filenames = ["M26BMI_00TCM mAs_vector_file.bin", ...
    "M26BMI_05TCM mAs_vector_file.bin", ...
    "M26BMI_10TCM mAs_vector_file.bin", ...
    "F25BMI_00TCM mAs_vector_file.bin", ...
    "F25BMI_05TCM mAs_vector_file.bin", ...
    "F25BMI_10TCM mAs_vector_file.bin", ...
    "F41BMI_00TCM mAs_vector_file.bin", ...
    "F41BMI_05TCM mAs_vector_file.bin", ...
    "F41BMI_10TCM mAs_vector_file.bin"];

image_filenames = ["coronal_M26.jpg", ...
    "coronal_F25.jpg", ...
    "coronal_F41c.jpg"];

plot_titles = ["Male 26 BMI", "Female 25 BMI", "Female 41 BMI"];

%% Make plot

[fig1, sums] = plotTiledBinaryWithBackground(data_filenames, image_filenames, plot_titles, true);
% Corresponds to rectangular filter of...

fig1.Units = 'pixels';
fig1.Position = [100 100 2000 475];

drawnow;  % ensures layout is finalized

exportgraphics(fig1, 'mAs_profile_figure.png', 'Resolution', 300);


