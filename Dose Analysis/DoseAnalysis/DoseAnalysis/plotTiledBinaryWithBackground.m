function [fig, sums] = plotTiledBinaryWithBackground(dataFiles, bgImageFiles, plotTitles, legend_bool)
% plotTiledBinaryWithBackground
%
% Inputs:
%   dataFiles     - string or char array, length 9
%                   (3 curves per plot, ordered by plot)
%   bgImageFiles  - string or char array, length 3
%   plotTitles    - string or char array, length 3
%
% Example ordering of dataFiles:
%   dataFiles(1:3)   -> plot 1 (red, yellow, green)
%   dataFiles(4:6)   -> plot 2
%   dataFiles(7:9)   -> plot 3

    % --------- Basic validation ----------
    if numel(dataFiles) ~= 9
        error('dataFiles must contain exactly 9 filenames.');
    end
    if numel(bgImageFiles) ~= 3
        error('bgImageFiles must contain exactly 3 filenames.');
    end
    if numel(plotTitles) ~= 3
        error('plotTitles must contain exactly 3 titles.');
    end

    % --------- Setup figure and layout ----------
    fig = figure;
    t = tiledlayout(1, 3, 'TileSpacing','compact', 'Padding','compact');

    % Curve colors: red, yellow, green
    curveColors = [
        1 0 0;    % red
        1 1 0;    % yellow
        0 1 0     % green
    ];
    sums = [];
    % --------- Loop over the three plots ----------
    for p = 1:3
        ax = nexttile(t);
        hold(ax, 'on');
        
        % ----- Load background image -----
        bgImg = imread(bgImageFiles(p));
        
        % ----- Load all three curves first (so we know axis limits) -----
        curves = cell(1,3);
        xMax = 0;
        yMin = inf;
        yMax = -inf;
        
        for c = 1:3
            idx = (p-1)*3 + c;
        
            fid = fopen(dataFiles(idx), 'rb');

            % Open binary mAs profile and downsample by averaging
            y = fread(fid, inf, 'float32');   
            fclose(fid);
           
            % Compute sum of all elements
            sums(end + 1) = sum(y(:)); 


            % ---- SMOOTHING ----
            % y = movmean(y, windowSize);



            
            % Define new x-axis
            x = 1:numel(y);
        
            curves{c} = struct('x', x, 'y', y);
        
            xMax = max(xMax, max(x));
            yMin = min(yMin, min(y));
            yMax = max(yMax, max(y));
        end

        % ----- Draw background image FULLY spanning the plot axes -----
        hImg = imagesc(ax, ...
            [1 xMax], ...        % X span
            [0 700], ...     % Y span
            bgImg);
        
        set(ax, 'YDir', 'normal');  % important for correct orientation
        uistack(hImg, 'bottom');
        colormap(ax, gray); % keeps image from showing up blue
        
        % Optional: transparency so curves stand out
        set(hImg, 'AlphaData', 0.9);
        
        % ----- Plot curves on top -----
        for c = 1:3
            plot(ax, curves{c}.x, curves{c}.y, ...
                'Color', curveColors(c,:), ...
                'LineWidth', 1.5);
        end
        
        % ----- Labels -----
        title(ax, plotTitles(p), 'Interpreter','none', "FontSize", 22);
        xlabel(ax, 'Z', "FontSize", 18);
        ylabel(ax, 'mAs', "FontSize", 18);
        xticks([]);
        
        axis(ax, 'tight');
        box(ax, 'on');

        ylim([0 700]);
        hold(ax, 'off');

    end

    if legend_bool
        lgd = legend(ax, {"$\alpha = 0.0$", "$\alpha = 0.5$", "$\alpha = 1.0$"}, 'Interpreter', 'latex', 'Location','eastoutside', "FontSize", 24);

        % ----- Dark theme styling -----
        lgd.Color = [0.15 0.15 0.15];      % very dark gray background
        lgd.TextColor = [1 1 1];           % white text
        lgd.EdgeColor = [0.4 0.4 0.4];     % subtle border
        lgd.Box = 'on';


    end
end